"""Reproducible real-source and adversarial engineering acceptance suite."""
from pathlib import Path
import json
import shutil
import time
import numpy as np
import pyarrow.parquet as pq
from vla_pipeline.io import digest,write_json
from vla_pipeline.pipeline import run,verify_release

ROOT=Path(__file__).resolve().parents[1]

def main():
    start=time.perf_counter()
    manifest,cached=run(ROOT/'configs/demo_sources.lock.json',ROOT/'data',True)
    release=ROOT/'data/releases'/manifest['release_id']
    again,second_cached=run(ROOT/'configs/demo_sources.lock.json',ROOT/'data',True)
    assert again==manifest and second_cached
    q=json.loads((release/'quality.json').read_text());stats=json.loads((release/'statistics.json').read_text())
    for source,st in stats.items():
        allowed={r['episode_id'] for r in q['episodes'] if r['source_id']==source and r['split']=='train'}
        assert set(st['fit_episode_ids'])==allowed
    masks=0;windows=0;max_roundtrip=0.
    for p in (release/'views').rglob('*.npz'):
        with np.load(p,allow_pickle=False) as b:
            source=p.parent.parent.name;ep=p.stem
            raw=pq.read_table(release/'canonical'/source/(ep+'.parquet')).to_pylist()
            ac=np.asarray([r['action'] for r in raw])
            for i,t in enumerate(b['anchor_index']):
                valid=min(8,len(ac)-t);mask=b['action_mask'][i]
                assert mask[:valid].all() and not mask[valid:].any()
                restored=b['actions'][i,:valid]*stats[source]['action']['std']+stats[source]['action']['mean']
                max_roundtrip=max(max_roundtrip,float(np.max(np.abs(restored-ac[t:t+valid]))))
            masks+=int((~b['action_mask']).sum());windows+=len(b['anchor_index'])
    # Create explicit derived fixtures from one actual G1 numeric episode + video.
    # These are test corruptions, never counted as additional real demonstrations.
    testroot=ROOT/'data/acceptance-fixtures';rawroot=testroot/'raw/injected/v1';rawroot.mkdir(parents=True,exist_ok=True)
    source=json.loads((ROOT/'configs/demo_sources.lock.json').read_text())['sources'][0]
    sourcebase=ROOT/'data/raw'/source['id']/source['revision']
    video=next(x['path'] for x in source['files'] if x['path'].endswith('episode_000000.mp4'))
    shutil.copy2(sourcebase/video,rawroot/'video.mp4')
    rows=pq.read_table(release/'canonical/g1_real/0.parquet').to_pylist()
    base={'episode_id':'good','origin_group':'injected:0','fps':20,'video':'video.mp4','steps':[{'timestamp':r['timestamp'],'state':r['state'],'action':r['action'],'language':r['language']} for r in rows]}
    fixtures=[]
    for name in ['good','duplicate','bad_time','bad_nan','bad_video']:
        obj=json.loads(json.dumps(base));obj['episode_id']=name
        if name=='bad_time':obj['steps'][2]['timestamp']=0
        if name=='bad_nan':obj['steps'][0]['action'][0]=float('nan')
        if name=='bad_video':obj['video']='absent.mp4'
        # Deliberately non-standard NaN is an adversarial parser/quality input.
        (rawroot/(name+'.json')).write_text(json.dumps(obj))
        fixtures.append(name+'.json')
    files=[{'path':p.name,'bytes':p.stat().st_size,'sha256':digest(p)} for p in sorted(rawroot.iterdir()) if p.is_file()]
    lock={'sources':[{'id':'injected','label':'Deliberately corrupted test derivatives, not new real data','revision':'v1','format':'lab_json_v1','embodiment':'unitree_g1_43','origin_namespace':'injected','license':'CC-BY-4.0 (derived NVIDIA G1 fixture)','episode_files':fixtures,'files':files}]}
    write_json(testroot/'lock.json',lock)
    adverse,_=run(testroot/'lock.json',testroot,True)
    assert adverse['accepted_episodes']==1 and adverse['duplicate_episodes']==1 and adverse['quarantined_episodes']==3
    aq=json.loads((testroot/'releases'/adverse['release_id']/'quality.json').read_text())
    result={'release_id':manifest['release_id'],'accepted_real_source_episodes':manifest['accepted_episodes'],'numeric_frames':manifest['numeric_frames'],'training_windows':windows,'raw_download_bytes':manifest['raw_download_bytes'],'checks':{'offline_rerun_same_manifest':True,'cached_second_run':second_cached,'train_only_statistics':True,'all_action_windows_episode_bounded':True,'masked_padding_elements':masks,'action_normalization_roundtrip_max_abs_error':max_roundtrip,'output_integrity_verified':bool(verify_release(release))},'adversarial_fixture_result':{'origin':'Copies/corruptions of NVIDIA G1 episode 0, not extra real demonstrations','accepted':adverse['accepted_episodes'],'duplicates':adverse['duplicate_episodes'],'quarantined':adverse['quarantined_episodes'],'quarantine_details':aq['quarantined']},'sources':manifest['sources'],'elapsed_seconds':round(time.perf_counter()-start,3)}
    write_json(ROOT/'reports/acceptance.json',result)
    # Report evidence excludes absolute machine paths and bulk numeric training data.
    write_json(ROOT/'reports/pipeline_manifest.json',manifest)
    write_json(ROOT/'reports/episode_quality.json',q)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
