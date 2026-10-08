"""Optional real official-SDK acceptance, in the separate pinned SDK environment."""
import argparse
import importlib.metadata
from pathlib import Path
import json
import platform
import shutil
import numpy as np
import av
import torch
from torch.utils.data import DataLoader
from vla_pipeline.io import write_json, digest
from vla_pipeline.lerobot_export import export_lerobot


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    parser.add_argument('--raw-root', type=Path, required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--report-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_root.exists():
        raise FileExistsError('Use a fresh SDK export output-root')
    torch.set_num_threads(1)
    av.logging.set_level(av.logging.ERROR)
    from lerobot.datasets.lerobot_dataset import LeRobotDataset
    from resource_status import snapshot
    resources = [{'phase': 'before', 'snapshot': snapshot()}]
    results = []
    for split in ('train', 'validation'):
        output = args.output_root / split
        repo_id = 'local/' + args.source + '-' + split
        receipt = export_lerobot(args.release, args.raw_root, args.source, split, output, repo_id)
        fps = int(json.loads((output / 'meta/info.json').read_text(encoding='utf-8'))['fps'])
        horizon = 8
        reader = LeRobotDataset(repo_id=repo_id, root=output, video_backend='pyav', delta_timestamps={'action': [i / fps for i in range(horizon)]})
        offset = 0; max_error = 0.; boundaries = []
        for ep in receipt['episodes']:
            length = ep['frames']
            first = reader[offset]; tail = reader[offset + length - 1]
            assert first['action'].shape[0] == horizon and first['action_is_pad'].shape == (horizon,)
            assert not bool(first['action_is_pad'][0])
            assert not bool(tail['action_is_pad'][0]) and bool(tail['action_is_pad'][1:].all())
            boundaries.append({'episode_index': ep['export_episode_index'], 'start': offset, 'length': length,
                               'last_frame_pad_mask': tail['action_is_pad'].tolist()})
            # The last action chunk must pad with this episode's last action, not next episode data.
            assert torch.allclose(tail['action'], tail['action'][0].expand_as(tail['action']))
            offset += length
        batch = next(iter(DataLoader(reader, batch_size=2, shuffle=False, num_workers=0)))
        for key in ('observation.images.main', 'observation.state', 'action'):
            assert bool(torch.isfinite(batch[key]).all())
        # Compare SDK native actions against the canonical source labels for every episode.
        import pyarrow.parquet as pq
        all_actions = np.asarray(reader.hf_dataset.with_format('numpy', columns=['action'])[:]['action'], dtype=np.float64)
        for ep, boundary in zip(receipt['episodes'], boundaries):
            rows = pq.read_table(args.release / 'canonical' / args.source / (ep['source_episode_id'] + '.parquet')).to_pylist()
            expected = np.asarray([row['action'] for row in rows], dtype=np.float64)
            actual = all_actions[boundary['start']:boundary['start'] + boundary['length']]
            max_error = max(max_error, float(np.max(np.abs(actual - expected))))
        assert max_error < 1e-5
        receipt['official_action_chunk_horizon'] = horizon
        receipt['official_episode_boundary_padding_checked'] = boundaries
        receipt['canonical_label_roundtrip_max_abs_error'] = max_error
        receipt['official_batch_shapes'] = {k: list(v.shape) for k, v in batch.items() if isinstance(v, torch.Tensor)}
        receipt['all_frame_action_labels_checked'] = True
        for name in ('source_lock.json', 'recipe.json', 'statistics.json'):
            shutil.copy2(args.release / name, output / ('pipeline_' + name))
        write_json(output / 'pipeline_export_receipt.json', receipt)
        receipt['export_output_sha256'] = {path.relative_to(output).as_posix(): digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
        write_json(args.report_dir / (args.source + '-' + split + '-sdk.json'), receipt)
        results.append(receipt)
        print(split, 'official SDK frames:', len(reader), 'batch action:', list(batch['action'].shape), flush=True)
    resources.append({'phase': 'after', 'snapshot': snapshot()})
    packages = {d.metadata['Name']: d.version for d in importlib.metadata.distributions()}
    write_json(args.report_dir / (args.source + '-sdk-environment.json'), {'platform': platform.platform(), 'python': platform.python_version(),
               'packages': dict(sorted(packages.items())), 'scope': 'Only this OS/architecture was executed; resolve and verify target-platform dependencies separately', 'resource_snapshots': resources})
    write_json(args.report_dir / (args.source + '-sdk-summary.json'), {'results': results, 'model_training_performed': False, 'robot_control_performed': False})

if __name__ == '__main__':
    main()
