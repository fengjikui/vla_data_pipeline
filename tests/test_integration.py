import copy
import json
from pathlib import Path
import av
import numpy as np
import pytest
from vla_pipeline.io import write_json
from vla_pipeline.pipeline import run,verify_release
from vla_pipeline.register import register_local
from vla_pipeline.quality import assign_split


def make_local_fixture(path):
    path.mkdir(parents=True,exist_ok=True)
    with av.open(str(path/'video.mp4'),'w') as out:
        stream=out.add_stream('mpeg4',rate=20);stream.width=64;stream.height=64;stream.pix_fmt='yuv420p'
        for i in range(20):
            frame=av.VideoFrame.from_ndarray(np.full((64,64,3),i*10,np.uint8),format='rgb24')
            for packet in stream.encode(frame):out.mux(packet)
        for packet in stream.encode():out.mux(packet)
    descriptor={'id':'local_fixture','label':'Synthetic contract test; not collected robot data','format':'lab_json_v1','revision':'v1','embodiment':'test_fixture','origin_namespace':'test','license':'test-only','environment':'synthetic_test','collection':'generated_test_fixture','semantics_status':'unknown','episode_files':[]}
    for i in range(8):
        item={'episode_id':str(i),'origin_group':f'test:{i}','fps':20,'video':'video.mp4','steps':[{'timestamp':t/20,'state':[float(i),t/20],'action':[float(i)+t/10,1.],'language':'fixture task'} for t in range(20)]}
        name=f'{i}.json';write_json(path/name,item);descriptor['episode_files'].append(name)
    duplicate=json.loads((path/'0.json').read_text());duplicate['episode_id']='duplicate';write_json(path/'duplicate.json',duplicate)
    bad=copy.deepcopy(duplicate);bad['episode_id']='bad';bad['steps'][2]['timestamp']=0;write_json(path/'bad.json',bad)
    descriptor['episode_files']+=['duplicate.json','bad.json']
    write_json(path/'source.json',descriptor)
    return descriptor


def test_local_ingest_quarantine_dedup_incremental_and_idempotence(tmp_path):
    incoming=tmp_path/'incoming';root=tmp_path/'store';lock=tmp_path/'lock.json'
    descriptor=make_local_fixture(incoming)
    register_local(incoming,incoming/'source.json',root,lock)
    result,cached=run(lock,root,offline=True)
    assert not cached and result['accepted_episodes']==8
    assert result['duplicate_episodes']==1 and result['quarantined_episodes']==1
    first=root/'releases'/result['release_id'];q=json.loads((first/'quality.json').read_text())
    assert q['quarantined'][0]['stage']=='quality'
    result2,cached=run(lock,root,offline=True)
    assert cached and result2==result
    before={x['episode_id']:x['split'] for x in q['episodes']}
    new=json.loads((incoming/'0.json').read_text());new['episode_id']='new';new['origin_group']='test:new'
    new['steps'][0]['state'][0]=100.;write_json(incoming/'new.json',new)
    descriptor['episode_files'].append('new.json');write_json(incoming/'source.json',descriptor)
    register_local(incoming,incoming/'source.json',root,lock)
    result3,_=run(lock,root,offline=True)
    assert result3['release_id']!=result['release_id'] and result3['accepted_episodes']==9
    latest=root/'releases'/result3['release_id'];q2=json.loads((latest/'quality.json').read_text())
    assert all(before[e['episode_id']]==e['split'] for e in q2['episodes'] if e['episode_id'] in before)
    verify_release(first);verify_release(latest)
    with pytest.raises(ValueError,match='Only interface_smoke'):run(lock,root,True,{'view':'action_bc'})


def test_raw_revision_collision_requires_new_revision(tmp_path):
    incoming=tmp_path/'incoming';root=tmp_path/'store';make_local_fixture(incoming)
    register_local(incoming,incoming/'source.json',root,tmp_path/'lock.json')
    item=json.loads((incoming/'0.json').read_text());item['steps'][0]['state'][0]=222;write_json(incoming/'0.json',item)
    with pytest.raises(ValueError,match='new revision'):register_local(incoming,incoming/'source.json',root,tmp_path/'lock.json')
