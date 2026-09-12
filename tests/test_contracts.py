import json
from dataclasses import replace
from pathlib import Path
import numpy as np
import pytest
from vla_pipeline.io import confined,fetch,write_json,digest
from vla_pipeline.readers import Episode,language_at_time
from vla_pipeline.quality import check_episode,assign_split,fit_stats,action_chunk,trajectory_fingerprint
from vla_pipeline.media import past_indices
from vla_pipeline.pipeline import validate_lock,verify_release


def episode(tmp_path):
    p=tmp_path/'video.mp4';p.write_bytes(b'placeholder')
    return Episode('source','0','original:0','robot',20,np.arange(4)/20,np.ones((4,2)),np.arange(8).reshape(4,2).astype(float),['task']*4,p)

@pytest.mark.parametrize('issue',['nan_action','infinite_state','backwards','duplicate_time','missing_language','missing_video','unsafe_id','bad_shape'])
def test_quality_blocks_invalid_input(tmp_path,issue):
    e=episode(tmp_path)
    if issue=='nan_action':e.action[0,0]=np.nan
    elif issue=='infinite_state':e.state[0,0]=np.inf
    elif issue=='backwards':e.timestamps=e.timestamps[::-1]
    elif issue=='duplicate_time':e.timestamps[1]=e.timestamps[0]
    elif issue=='missing_language':e.language[1]=''
    elif issue=='missing_video':e.video=None
    elif issue=='unsafe_id':e.episode_id='../escape'
    else:e.action=e.action[:2]
    assert check_episode(e)['errors']


def test_unknown_quality_is_not_success(tmp_path):
    e=episode(tmp_path);q=check_episode(e)
    assert not q['errors'] and not q['deployment_ready'] and e.success is None
    assert 'success_unknown_not_assumed_expert' in q['warnings']


def test_causal_language_does_not_see_future():
    anns=[{'content':'grasp','timestamp':0},{'content':'release','timestamp':5}]
    assert language_at_time('task',anns,1)=='task | grasp'
    assert language_at_time('task',anns,-1)=='task'
    assert language_at_time('task',anns,5)=='task | release'


def test_past_frame_not_nearest_future():
    assert past_indices([0,.05,.1],[.049,.099],.1).tolist()==[0,1]
    with pytest.raises(ValueError):past_indices([.05],[0],.1)
    with pytest.raises(ValueError):past_indices([0],[1],.1)


def test_chunk_tail_mask_and_no_episode_crossing():
    a=np.arange(12).reshape(6,2)
    chunk,mask=action_chunk(a,5,8)
    assert mask.sum()==2 and np.array_equal(chunk[0],a[-1])
    assert not chunk[1:].any() and not mask[1:].any()


def test_stats_use_only_train_and_roundtrip(tmp_path):
    e=episode(tmp_path);v=replace(e,episode_id='1',action=np.full((4,2),1e9))
    stats=fit_stats([(e,'train'),(v,'validation')])
    assert stats['action']['mean']==[3,4]
    norm=(e.action-stats['action']['mean'])/stats['action']['std']
    assert np.allclose(norm*stats['action']['std']+stats['action']['mean'],e.action)
    with pytest.raises(ValueError):fit_stats([(v,'validation')])


def test_incremental_split_stability_and_same_origin():
    old={g:assign_split(g) for g in ['source:0','source:1','source:2']}
    new={g:assign_split(g) for g in ['source:0','source:1','source:2','source:3']}
    assert all(new[g]==s for g,s in old.items())
    assert assign_split('original:1')==assign_split('original:1')


def test_numeric_dedup_ignores_recaptions(tmp_path):
    e=episode(tmp_path);recaption=replace(e,source_id='another',episode_id='100',language=['different']*4)
    assert trajectory_fingerprint(e)==trajectory_fingerprint(recaption)


def test_path_traversal_and_symlink(tmp_path):
    with pytest.raises(ValueError):confined(tmp_path,'../escaped')
    (tmp_path/'link').symlink_to(tmp_path.parent)
    with pytest.raises(ValueError):confined(tmp_path,'link/escaped')


def test_hash_corruption_fails_closed(tmp_path):
    p=tmp_path/'x';p.write_bytes(b'corrupt')
    with pytest.raises(ValueError):fetch('',p,100,'a'*64,True)
    with pytest.raises(FileNotFoundError):fetch('',tmp_path/'missing',100,None,True)


def test_release_integrity(tmp_path):
    (tmp_path/'data').write_text('ok');write_json(tmp_path/'manifest.json',{'output_sha256':{'data':digest(tmp_path/'data')}})
    verify_release(tmp_path);(tmp_path/'data').write_text('broken')
    with pytest.raises(ValueError):verify_release(tmp_path)


def test_duplicate_source_ids_rejected():
    s={'id':'x','origin_namespace':'o','revision':'r','license':'test','files':[]}
    with pytest.raises(ValueError):validate_lock({'sources':[s,s]})
