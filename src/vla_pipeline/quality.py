"""Data checks are separate from task success and deployment compatibility."""
import numpy as np
from .io import object_hash


def check_episode(ep):
    errors=[];warnings=[]
    n=len(ep.timestamps)
    if not ep.episode_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in ep.episode_id):errors.append('unsafe_episode_id')
    if n<2:errors.append('too_few_steps')
    if not np.isfinite(ep.fps) or ep.fps<=0:errors.append('invalid_fps')
    if ep.timestamps.ndim!=1 or not np.isfinite(ep.timestamps).all():errors.append('invalid_timestamps')
    elif np.any(np.diff(ep.timestamps)<=0):errors.append('non_monotonic_time')
    for key in ('state','action'):
        value=getattr(ep,key)
        if value.ndim!=2 or len(value)!=n or (value.ndim==2 and value.shape[1]==0):errors.append(f'{key}_shape')
        elif not np.isfinite(value).all():errors.append(f'{key}_non_finite')
    if len(ep.language)!=n or any(not isinstance(t,str) or not t.strip() for t in ep.language):errors.append('missing_language')
    if not ep.origin_group:errors.append('missing_origin_group')
    if ep.video is None or not ep.video.is_file():errors.append('missing_video')
    if ep.semantics_status!='verified':warnings.append('action_semantics_not_deployment_verified')
    if ep.success is None:warnings.append('success_unknown_not_assumed_expert')
    if n>1 and np.isfinite(ep.fps) and ep.fps>0 and np.any(np.abs(np.diff(ep.timestamps)-1/ep.fps)>0.15/ep.fps):warnings.append('irregular_sample_intervals')
    return {'errors':errors,'warnings':warnings,'deployment_ready':False,'eligible_view':'interface_smoke' if not errors else None}


def trajectory_fingerprint(ep):
    # Numeric exact duplicate detection within an embodiment; media/text are deliberately
    # excluded so a recaption/re-encode cannot escape a group split. Near-duplicates remain future work.
    return object_hash({'embodiment':ep.embodiment,'time':ep.timestamps.tolist(),'state':ep.state.tolist(),'action':ep.action.tolist()})


def assign_split(group,seed='lab-demo-v1'):
    return 'validation' if int(object_hash({'group':group,'seed':seed})[:8],16)%5==0 else 'train'


def fit_stats(episodes):
    train=[ep for ep,split in episodes if split=='train']
    if not train:raise ValueError('No training episodes; refusing validation-derived statistics')
    result={}
    for key in ('state','action'):
        values=np.concatenate([getattr(ep,key) for ep in train])
        result[key]={'mean':values.mean(0).tolist(),'std':np.maximum(values.std(0),1e-6).tolist(),'count':len(values)}
    result['fit_episode_ids']=[e.episode_id for e in train]
    return result


def action_chunk(actions,t,horizon):
    d=actions.shape[1];out=np.zeros((horizon,d),np.float32);mask=np.zeros((horizon,d),bool)
    valid=min(horizon,len(actions)-t)
    out[:valid]=actions[t:t+valid];mask[:valid]=True
    return out,mask
