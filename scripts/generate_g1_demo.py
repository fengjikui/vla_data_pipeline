"""Generate tiny synthetic XR-shaped data. No real G1 joint mapping or motion."""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image
from vla_pipeline.io import write_json


def generate(root, episodes=8, frames=24):
    root = Path(root)
    if root.exists():
        raise FileExistsError('Use a fresh demo directory')
    capture = root / 'capture'
    groups = {}
    for episode in range(episodes):
        ep = capture / 'demo_task' / f'episode_{episode:04d}'
        (ep / 'colors').mkdir(parents=True)
        rows = []
        for index in range(frames):
            rel = f'colors/{index:06d}_color_0.jpg'
            image = np.zeros((64, 64, 3), np.uint8)
            image[:, :, 0] = episode * 23
            image[:, :, 1] = index * 9 % 256
            image[8:24, (index % 32):(index % 32 + 16), 2] = 230
            Image.fromarray(image).save(ep / rel)
            state = [episode / 10 + index / 100, index / 20]
            action = [state[0] + .02, state[1] + .04]
            rows.append({'idx': index, 'colors': {'color_0': rel}, 'depths': {}, 'audios': {},
                         'states': {'left_arm': {'qpos': state}}, 'actions': {'left_arm': {'qpos': action}}})
        write_json(ep / 'data.json', {'info': {'version': '1.0.0', 'image': {'width': 64, 'height': 64, 'fps': 20}, 'joint_names': {'left_arm': []}},
                                      'text': {'goal': '合成教学：将方块移动到标记处'}, 'data': rows})
        # Distinct synthetic sessions: this does not demonstrate scene generalization.
        groups[f'demo_task/episode_{episode:04d}/data.json'] = f'g1-synthetic:session-{episode}'
    mapping = {'schema': 'unitree_xr_mapping_v1', 'source': {'id': 'g1_edu_synthetic', 'label': 'XR-shaped synthetic fixture, NOT G1 collected data',
               'revision': 'batch-001', 'embodiment': 'synthetic_two_channels_NOT_real_G1', 'origin_namespace': 'g1-synthetic',
               'license': 'generated engineering fixture; no robot capability evidence', 'environment': 'synthetic_test', 'collection': 'generated_test_fixture'},
               'camera': 'color_0', 'timing': {'mode': 'nominal_index'}, 'state_fields': [{'path': 'states.left_arm.qpos', 'names': ['demo_0', 'demo_1'], 'unit': 'synthetic_unit'}],
               'action_fields': [{'path': 'actions.left_arm.qpos', 'names': ['demo_0', 'demo_1'], 'unit': 'synthetic_unit'}],
               'action_contract': {'type': 'synthetic_absolute_target', 'controller': 'none', 'deployment_ready': False}, 'origin_groups': groups}
    write_json(root / 'mapping.json', mapping)
    return mapping

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); generate(args.output); print('Generated synthetic fixture:', args.output)
