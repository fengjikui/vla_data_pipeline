"""Source-specific readers. Native action meanings are preserved, never guessed."""
from __future__ import annotations
from dataclasses import dataclass, field
import json
from pathlib import Path
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from .io import confined


@dataclass
class Episode:
    source_id: str
    episode_id: str
    origin_group: str
    embodiment: str
    fps: float
    timestamps: np.ndarray
    state: np.ndarray
    action: np.ndarray
    language: list[str]
    video: Path | None
    video_offset: float = 0.0
    video_end: float | None = None
    state_names: list[str] = field(default_factory=list)
    action_names: list[str] = field(default_factory=list)
    semantics_status: str = 'unknown'
    success: bool | None = None
    extras: dict = field(default_factory=dict)


def feature_names(info, key):
    names=info['features'][key].get('names')
    return names if isinstance(names,list) and all(isinstance(x,str) for x in names) else []


def language_at_time(task, annotations, timestamp):
    if isinstance(annotations,str):
        return task+' '+annotations if annotations.strip() else task
    if isinstance(annotations,list):
        visible=[a for a in annotations if isinstance(a,dict) and isinstance(a.get('timestamp'),(int,float)) and a['timestamp']<=timestamp and isinstance(a.get('content'),str)]
        if visible:
            return task+' | '+max(visible,key=lambda a:a['timestamp'])['content']
    return task


def read_lerobot(spec: dict, raw_root: Path):
    root=confined(raw_root,spec['id']+'/'+spec['revision'])
    base=confined(root,spec.get('subset',''))
    info=json.loads((base/'meta/info.json').read_text())
    is_v3=spec['format']=='lerobot_v3'
    version=info.get('codebase_version','')
    if (is_v3 and not version.startswith('v3')) or (not is_v3 and not version.startswith('v2')):
        raise ValueError(f'Unsupported source version: {version}')
    if is_v3:
        tasks={int(row['task_index']):str(row['task']) for row in pq.read_table(base/'meta/tasks.parquet').to_pylist()}
        metadata={int(x['episode_index']):x for x in pq.read_table(base/'meta/episodes/chunk-000/file-000.parquet').to_pylist()}
    else:
        tasks={int(x['task_index']):x['task'] for x in (json.loads(l) for l in (base/'meta/tasks.jsonl').read_text().splitlines() if l.strip())}
        metadata={int(x['episode_index']):x for x in (json.loads(l) for l in (base/'meta/episodes.jsonl').read_text().splitlines() if l.strip())}
    for e in spec['episodes']:
        try:
            meta=metadata[e]
            if is_v3:
                data_rel=info['data_path'].format(chunk_index=meta['data/chunk_index'],file_index=meta['data/file_index'])
                table=pq.read_table(confined(base,data_rel),filters=[('episode_index','=',e)])
                video_rel=info['video_path'].format(video_key=spec['camera'],chunk_index=meta[f'videos/{spec["camera"]}/chunk_index'],file_index=meta[f'videos/{spec["camera"]}/file_index'])
                offset=float(meta[f'videos/{spec["camera"]}/from_timestamp'])
                end=float(meta[f'videos/{spec["camera"]}/to_timestamp'])
            else:
                data_rel=info['data_path'].format(episode_chunk=e//info['chunks_size'],episode_index=e)
                table=pq.read_table(confined(base,data_rel))
                video_rel=info['video_path'].format(episode_chunk=e//info['chunks_size'],episode_index=e,video_key=spec['camera'])
                offset=0.0;end=None
            rows=table.to_pylist()
            if not rows or any(int(r['episode_index'])!=e for r in rows):raise ValueError('Episode boundary mismatch')
            if len(rows)!=int(meta['length']):raise ValueError('Episode length disagrees with metadata')
            if 'frame_index' in rows[0] and [int(r['frame_index']) for r in rows]!=list(range(len(rows))):raise ValueError('Non-contiguous frame index')
            # Preserve language by row, including events where present, rather than one global task.
            language=[]
            for row in rows:
                task=tasks.get(int(row['task_index']))
                if task is None:raise ValueError('Unresolved task_index')
                task=language_at_time(task,row.get('language_persistent'),float(row['timestamp']))
                language.append(task)
            st=np.asarray([r['observation.state'] for r in rows],dtype=np.float64)
            ac=np.asarray([r['action'] for r in rows],dtype=np.float64)
            if st.shape[1:]!=tuple(info['features']['observation.state']['shape']) or ac.shape[1:]!=tuple(info['features']['action']['shape']):raise ValueError('Shape disagrees with source metadata')
            yield Episode(spec['id'],str(e),f'{spec["origin_namespace"]}:{e}',spec['embodiment'],float(info['fps']),np.asarray([r['timestamp'] for r in rows]),st,ac,language,confined(base,video_rel),offset,end,feature_names(info,'observation.state'),feature_names(info,'action'),spec.get('semantics_status','unknown'),extras={'source_data_path':data_rel,'source_columns':table.column_names,'source_split':'train','timestamp_basis':'source_episode_seconds','alignment_assumption':'video PTS and robot timestamps share source clock; availability latency unverified','source_episode_index':e})
        except (ValueError,KeyError,FileNotFoundError,pa.ArrowException) as exc:
            yield {'source_id':spec['id'],'episode_id':str(e),'stage':'parse','reason':str(exc)}


def read_local_json(spec: dict, raw_root: Path):
    """Self-collected JSON contract. Media paths remain confined to this source root."""
    root=confined(raw_root,spec['id']+'/'+spec['revision'])
    for rel in spec['episode_files']:
        try:
            item=json.loads(confined(root,rel).read_text())
            rows=item['steps']
            yield Episode(spec['id'],str(item['episode_id']),item['origin_group'],spec['embodiment'],float(item['fps']),np.asarray([r['timestamp'] for r in rows],float),np.asarray([r['state'] for r in rows],float),np.asarray([r['action'] for r in rows],float),[r['language'] for r in rows],confined(root,item['video']) if item.get('video') else None,float(item.get('video_offset',0)),semantics_status=spec.get('semantics_status','unknown'),success=item.get('success'),extras={'source_data_path':rel,'alignment_assumption':item.get('alignment_assumption','unverified')})
        except (ValueError,KeyError,TypeError,OSError) as exc:
            yield {'source_id':spec['id'],'episode_id':rel,'stage':'parse','reason':str(exc)}


def read_source(spec,raw_root):
    if spec['format'] in ('lerobot_v2','lerobot_v3'):return read_lerobot(spec,raw_root)
    if spec['format']=='lab_json_v1':return read_local_json(spec,raw_root)
    raise ValueError('Unsupported adapter: '+spec['format'])
