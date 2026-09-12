"""Create a pinned source lock from public official repositories. Refresh is explicit.
The pipeline downloads from the committed lock; this script is only for maintainers.
"""
import concurrent.futures
import json
from pathlib import Path
import urllib.request
from vla_pipeline.io import fetch, write_json

ROOT = Path(__file__).resolve().parents[1]
SPECS = [
 dict(id='g1_real', label='真实人形 G1 上身遥操作', repo='nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1', revision='0d7bdd06e67f3ca0868892d0ec8f03bcd3e49e40', subset='g1-pick-apple', camera='observation.images.ego_view', format='lerobot_v2', embodiment='unitree_g1_43', environment='real', collection='teleoperation', license='CC-BY-4.0', origin_namespace='nvidia-g1-apple', semantics_status='partial', action_type='source_joint_targets', units='source_native_unverified', semantic_note='43 named joints retained. Position target interpretation requires controller confirmation. Upper-body demonstrations do not establish locomotion skill.'),
 dict(id='abc_real', label='真实双臂 YAM 遥操作', repo='lerobot/abc_130k_v3_smoke', revision='b342a0ff262195d49bae3eece6e3f40c6e1dbe15', subset='', camera='observation.images.top', format='lerobot_v3', embodiment='yam_bimanual_14', environment='real', collection='teleoperation', license='Apache-2.0', origin_namespace='abc130k-smoke', semantics_status='partial', action_type='source_native_14d', units='source_native_unverified', semantic_note='14 native dimensions retained. Original ABC episode lineage and gripper/controller semantics need upstream confirmation before cross-source mixing or deployment.'),
 dict(id='panda_sim', label='仿真双臂 Panda 穿引任务', repo='nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim', revision='ea7ac0b68f87da62f1e726771bba0fe74300802f', subset='bimanual_panda_gripper.Threading', camera='observation.images.front_view', format='lerobot_v2', embodiment='panda_sim_state32_action14', environment='simulation', collection='source_sim_demonstrations', license='CC-BY-4.0', origin_namespace='nvidia-panda-threading', semantics_status='partial', action_type='source_controller_action_14d', units='source_native_unverified', semantic_note='State 32 / action 14 are not interchangeable. Generic motor labels do not establish joint-space meaning; simulator controller mapping still needs verification.')
]

def prepare(spec):
    spec = dict(spec, episodes=list(range(6)), fps=None, source_url='https://huggingface.co/datasets/'+spec['repo'])
    pre = spec['subset']+'/' if spec['subset'] else ''
    paths = ['README.md', pre+'meta/info.json']
    if spec['format'] == 'lerobot_v2':
        paths += [pre+'meta/tasks.jsonl',pre+'meta/episodes.jsonl',pre+'meta/modality.json']
        for e in spec['episodes']:
            paths += [pre+f'data/chunk-000/episode_{e:06d}.parquet', pre+f'videos/chunk-000/{spec["camera"]}/episode_{e:06d}.mp4']
    else:
        paths += ['meta/tasks.parquet','meta/episodes/chunk-000/file-000.parquet','data/chunk-000/file-000.parquet',f'videos/{spec["camera"]}/chunk-000/file-000.mp4']
    records=[]
    for rel in paths:
        url=f'https://huggingface.co/datasets/{spec["repo"]}/resolve/{spec["revision"]}/{rel}'
        dst=ROOT/'data/raw'/spec['id']/spec['revision']/rel
        item=fetch(url,dst,180*1024*1024)
        records.append(dict(path=rel,url=url,**item))
        print(spec['id'],rel,item['bytes'],flush=True)
    spec['files']=records
    spec['fps']=json.loads((ROOT/'data/raw'/spec['id']/spec['revision']/pre/'meta/info.json').read_text())['fps']
    return spec

if __name__=='__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        sources=list(pool.map(prepare,SPECS))
    write_json(ROOT/'configs/demo_sources.lock.json',{'schema_version':'1.0','inspection_date':'2026-09-12','sample_scope':'First 6 episodes per source; one camera; v3 shared files contain additional unselected episodes. No whole-dataset audit.','sources':sources})
