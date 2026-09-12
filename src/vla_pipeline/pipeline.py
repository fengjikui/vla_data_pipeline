"""Auditable local batch pipeline, immutable releases, and model-specific views."""
from __future__ import annotations
from collections import Counter,defaultdict
from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import tempfile
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from PIL import Image
from .io import confined,digest,fetch,object_hash,write_json
from .readers import Episode,read_source
from .quality import check_episode,trajectory_fingerprint,assign_split,fit_stats,action_chunk
from .media import decode_at

VERSION='0.1.0'
DEFAULT_RECIPE={'schema':'training_view_v1','view':'interface_smoke','horizon':8,'anchor_stride':10,'max_anchors_per_episode':64,'image_size':64,'split_seed':'lab-demo-v1','pts_roundoff_tolerance_seconds':1e-6,'normalize':'per_source_train_only_zscore','action_rate':'source_native_no_resampling','limitations':['not a validated upstream VLA adapter','no hardware-clock latency calibration','unknown action semantics block deployment','holdout is episode-level engineering validation, not scene generalization']}


def code_hash():
    return object_hash({p.name:digest(p) for p in sorted(Path(__file__).parent.glob('*.py'))})


def validate_lock(lock):
    ids=[]
    for spec in lock['sources']:
        sid=spec['id']
        if not sid or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in sid):raise ValueError('Invalid source id')
        if not spec.get('origin_namespace') or not spec.get('license'):raise ValueError('Source provenance and license required')
        if not spec.get('revision') or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-' for c in spec['revision']):raise ValueError('Safe source revision required')
        for f in spec['files']:
            confined(Path('/tmp/source-root'),f['path'])
            if len(f['sha256'])!=64 or f['bytes']<0:raise ValueError('Invalid file lock')
        ids.append(sid)
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate source id')


def download(lock,raw_root,offline=False):
    validate_lock(lock)
    for spec in lock['sources']:
        for f in spec['files']:
            out=fetch(f.get('url',''),confined(raw_root/spec['id']/spec['revision'],f['path']),int(f['bytes']),f['sha256'],offline)
            if out['bytes']!=f['bytes']:raise ValueError('Source size mismatch')


def verify_release(path):
    manifest=json.loads((path/'manifest.json').read_text())
    for rel,sha in manifest['output_sha256'].items():
        if digest(confined(path,rel))!=sha:raise ValueError(f'Release corrupted: {rel}')
    return manifest


def run(lock_path,root,offline=False,recipe=None):
    lock=json.loads(Path(lock_path).read_text());recipe=dict(DEFAULT_RECIPE,**(recipe or {}))
    for key in ('horizon','anchor_stride','max_anchors_per_episode','image_size'):
        if not isinstance(recipe[key],int) or recipe[key]<=0:raise ValueError('Recipe values must be positive integers')
    if recipe['view']!='interface_smoke':raise ValueError('Only interface_smoke is implemented; production action_bc requires verified semantics and supervision')
    download(lock,root/'raw',offline)
    implementation=code_hash()
    release_id=object_hash({'lock':lock,'recipe':recipe,'code':implementation})[:24]
    dest=root/'releases'/release_id
    if dest.exists():
        manifest=verify_release(dest)
        write_json(root/'latest.json',{'release_id':release_id})
        return manifest,True
    dest.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.building-',dir=dest.parent))
    try:
        records=[];duplicates=[];quarantined=[];accepted=[];seen={}
        for spec in lock['sources']:
            for ep in read_source(spec,root/'raw'):
                if isinstance(ep,dict):quarantined.append(ep);continue
                q=check_episode(ep)
                if q['errors']:
                    quarantined.append({'source_id':ep.source_id,'episode_id':ep.episode_id,'stage':'quality','reasons':q['errors']});continue
                fingerprint=trajectory_fingerprint(ep)
                if fingerprint in seen:
                    duplicates.append({'source_id':ep.source_id,'episode_id':ep.episode_id,'same_numeric_trajectory_as':seen[fingerprint]});continue
                split=assign_split(ep.origin_group,recipe['split_seed'])
                n=len(ep.timestamps)
                anchors=np.unique(np.append(np.arange(0,n,recipe['anchor_stride']),n-1))
                if len(anchors)>recipe['max_anchors_per_episode']:
                    anchors=anchors[np.linspace(0,len(anchors)-1,recipe['max_anchors_per_episode']).astype(int)]
                try:rgb,pts,alignment=decode_at(ep,anchors,recipe['image_size'])
                except (ValueError,OSError,RuntimeError) as exc:
                    quarantined.append({'source_id':ep.source_id,'episode_id':ep.episode_id,'stage':'media','reason':str(exc)});continue
                seen[fingerprint]=f'{ep.source_id}:{ep.episode_id}'
                accepted.append((ep,split,anchors,rgb,pts))
                rec={'source_id':ep.source_id,'episode_id':ep.episode_id,'origin_group':ep.origin_group,'split':split,'embodiment':ep.embodiment,'frames':n,'anchors':len(anchors),'state_dim':ep.state.shape[1],'action_dim':ep.action.shape[1],'fps':ep.fps,'duration_seconds':float(ep.timestamps[-1]-ep.timestamps[0]),'task_first':ep.language[0],'task_last':ep.language[-1],'action_names':ep.action_names,'state_names':ep.state_names,'quality':q,'alignment':alignment,'fingerprint':fingerprint,'video_offset':ep.video_offset,'source_extras':ep.extras}
                records.append(rec)
                folder=staging/'canonical'/ep.source_id;folder.mkdir(parents=True,exist_ok=True)
                pq.write_table(pa.table({'timestamp':ep.timestamps,'state':ep.state.tolist(),'action':ep.action.tolist(),'language':ep.language}),folder/f'{ep.episode_id}.parquet')
                write_json(folder/f'{ep.episode_id}.json',rec)
                preview=staging/'previews'/ep.source_id;preview.mkdir(parents=True,exist_ok=True)
                Image.fromarray(rgb[0]).save(preview/f'{ep.episode_id}.jpg',quality=90)
        statistics={};source_reports=[]
        for spec in lock['sources']:
            group=[x for x in accepted if x[0].source_id==spec['id']]
            if not group:
                source_reports.append({'id':spec['id'],'accepted':0,'view_status':'no_eligible_episodes'});continue
            try:stats=fit_stats([(e,s) for e,s,*_ in group])
            except ValueError:
                source_reports.append({'id':spec['id'],'accepted':len(group),'view_status':'no_train_split'});continue
            statistics[spec['id']]=stats
            count=0
            for ep,split,anchors,rgb,pts in group:
                chunks=[action_chunk(ep.action,t,recipe['horizon']) for t in anchors]
                actions=np.stack([x[0] for x in chunks]);mask=np.stack([x[1] for x in chunks])
                state=((ep.state[anchors]-stats['state']['mean'])/stats['state']['std']).astype(np.float32)
                norm=((actions-stats['action']['mean'])/stats['action']['std']).astype(np.float32)
                norm[~mask]=0
                path=staging/'views'/spec['id']/split/f'{ep.episode_id}.npz';path.parent.mkdir(parents=True,exist_ok=True)
                np.savez_compressed(path,image=rgb,state=state,actions=norm,action_mask=mask,language=np.asarray([ep.language[t] for t in anchors]),anchor_index=anchors,timestamp=ep.timestamps[anchors],video_pts=pts)
                count+=len(anchors)
            source_reports.append({'id':spec['id'],'label':spec['label'],'accepted':len(group),'frames':sum(len(e.timestamps) for e,*_ in group),'training_windows':count,'splits':dict(Counter(s for _,s,*_ in group)),'view_status':'interface_smoke_only','state_dim':group[0][0].state.shape[1],'action_dim':group[0][0].action.shape[1]})
        write_json(staging/'statistics.json',statistics)
        write_json(staging/'quality.json',{'episodes':records,'quarantined':quarantined,'duplicates':duplicates,'sources':source_reports})
        write_json(staging/'source_lock.json',lock)
        write_json(staging/'recipe.json',recipe)
        outputs={p.relative_to(staging).as_posix():digest(p) for p in sorted(staging.rglob('*')) if p.is_file()}
        manifest={'release_id':release_id,'pipeline_version':VERSION,'code_sha256':implementation,'recipe':recipe,'sources':source_reports,'accepted_episodes':len(records),'quarantined_episodes':len(quarantined),'duplicate_episodes':len(duplicates),'numeric_frames':sum(r['frames'] for r in records),'training_windows':sum(r.get('training_windows',0) for r in source_reports),'raw_download_bytes':sum(f['bytes'] for s in lock['sources'] for f in s['files']),'source_lock_sha256':object_hash(lock),'output_sha256':outputs,'evidence_boundary':'engineering interface verification only; physical semantics and robot capability not validated'}
        if code_hash()!=implementation:raise RuntimeError('Code changed during pipeline run; rerun with a stable implementation')
        write_json(staging/'manifest.json',manifest)
        os.rename(staging,dest)
        write_json(root/'latest.json',{'release_id':release_id})
        return manifest,False
    finally:
        if staging.exists():shutil.rmtree(staging)
