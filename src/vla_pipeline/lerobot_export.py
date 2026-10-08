"""Optional bridge to the pinned official LeRobot SDK (not vendored).

Base pipeline tests do not certify upstream SDK integration. The SDK performs
its own dataset writing; this bridge never labels a homemade layout 'LeRobot'.
"""
from __future__ import annotations
import importlib.metadata
import json
from pathlib import Path
import subprocess
import av
import numpy as np
import pyarrow.parquet as pq
from .io import confined, digest, write_json
from .pipeline import verify_release
from .readers import read_source

SDK_COMMIT = 'ca69a2068462a37f7cdcb74180927a2f863d2bf7'


def export_plan(release, raw_root, source, split):
    release, raw_root = Path(release), Path(raw_root)
    manifest = verify_release(release)
    if split not in ('train', 'validation'):
        raise ValueError('Export one explicit split at a time')
    specs = json.loads((release / 'source_lock.json').read_text(encoding='utf-8'))['sources']
    spec = next((s for s in specs if s['id'] == source), None)
    if spec is None:
        raise ValueError('Unknown source')
    # Validate all raw inputs again before decoding, not just the canonical release.
    for item in spec['files']:
        path = confined(raw_root / spec['id'] / spec['revision'], item['path'])
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise ValueError('Raw source changed: ' + item['path'])
    records = json.loads((release / 'quality.json').read_text(encoding='utf-8'))['episodes']
    chosen = {r['episode_id']: r for r in records if r['source_id'] == source and r['split'] == split}
    if not chosen:
        raise ValueError('No accepted episodes in selected split')
    episodes = []
    for ep in read_source(spec, raw_root):
        if isinstance(ep, dict) or ep.episode_id not in chosen:
            continue
        # LeRobot regular cadence is checked without silently resampling timestamps.
        expected = np.arange(len(ep.timestamps)) / ep.fps
        if abs(ep.fps - round(ep.fps)) > 1e-9 or not np.allclose(ep.timestamps, expected, rtol=0, atol=1e-6):
            raise ValueError('Export requires integer FPS and zero-origin regular cadence; explicit resampling needed')
        canonical = pq.read_table(release / 'canonical' / source / (ep.episode_id + '.parquet')).to_pylist()
        if len(canonical) != len(ep.timestamps) or not np.allclose([r['action'] for r in canonical], ep.action):
            raise ValueError('Canonical/raw episode mismatch')
        episodes.append(ep)
    if len(episodes) != len(chosen):
        raise ValueError('Accepted episodes missing in raw replay')
    signatures = {(e.fps, e.embodiment, e.state.shape[1], e.action.shape[1], tuple(e.state_names), tuple(e.action_names)) for e in episodes}
    if len(signatures) != 1:
        raise ValueError('Mixed robot contracts require separate exports')
    return manifest, episodes


def causal_native_images(ep):
    """Decode full source RGB, sequentially; no future frame or image resize."""
    with av.open(str(ep.video)) as container:
        stream = container.streams.video[0]
        stream.codec_context.thread_count = 1
        container.seek(max(0, int((ep.video_offset - 1) / float(stream.time_base))), stream=stream, backward=True)
        decoded = iter(container.decode(stream))
        pending = None
        last = None
        last_time = None
        previous_pts = None
        tolerance = 1e-6
        for target in ep.timestamps + ep.video_offset:
            if ep.video_end is not None and target >= ep.video_end + tolerance:
                raise ValueError('Frame exceeds source episode boundary')
            while True:
                if pending is None:
                    try:
                        frame = next(decoded)
                    except StopIteration:
                        break
                    if frame.pts is None:
                        continue
                    pts = float(frame.pts * frame.time_base)
                    if previous_pts is not None and pts <= previous_pts:
                        raise ValueError('Non-monotonic source video')
                    previous_pts = pts
                    if pts < ep.video_offset - tolerance:
                        continue
                    pending = (pts, frame)
                if pending[0] > target + tolerance:
                    break
                last_time, frame = pending
                last = frame.to_ndarray(format='rgb24')
                pending = None
            if last is None or target - last_time > 1.5 / ep.fps:
                raise ValueError('Missing/stale source frame')
            yield last


def sdk_commit(module):
    for parent in Path(module.__file__).resolve().parents:
        if (parent / '.git').exists():
            return subprocess.check_output(['git', '-C', str(parent), 'rev-parse', 'HEAD'], text=True).strip()
    try:
        direct = json.loads(importlib.metadata.distribution('lerobot').read_text('direct_url.json') or '{}')
        return direct.get('vcs_info', {}).get('commit_id')
    except importlib.metadata.PackageNotFoundError:
        return None


def export_lerobot(release, raw_root, source, split, output, repo_id):
    manifest, episodes = export_plan(release, raw_root, source, split)
    # Import only after preflight: base users do not install robot/training dependencies.
    import torch
    torch.set_num_threads(1)
    import lerobot.datasets.lerobot_dataset as sdk
    from lerobot.configs.video import RGBEncoderConfig
    if sdk_commit(sdk) != SDK_COMMIT:
        raise ValueError('Install the exact official SDK commit documented in docs/16-training-export.md')
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError('Export output already exists; use a fresh directory')
    first = episodes[0]
    sample_image = next(causal_native_images(first))
    shape = tuple(sample_image.shape)
    state_names = first.state_names or [f'unverified_state_{i}' for i in range(first.state.shape[1])]
    action_names = first.action_names or [f'unverified_action_{i}' for i in range(first.action.shape[1])]
    camera = 'observation.images.main'
    features = {'observation.state': {'dtype': 'float32', 'shape': (first.state.shape[1],), 'names': state_names},
                'action': {'dtype': 'float32', 'shape': (first.action.shape[1],), 'names': action_names},
                camera: {'dtype': 'video', 'shape': shape, 'names': ['height', 'width', 'channels']}}
    dataset = sdk.LeRobotDataset.create(repo_id=repo_id, root=output, fps=round(first.fps), robot_type=first.embodiment,
                                        features=features, use_videos=True, image_writer_processes=0, image_writer_threads=1, encoder_threads=1,
                                        rgb_encoder=RGBEncoderConfig(vcodec='h264', crf=23, preset='veryfast', video_backend='pyav'))
    provenance = []
    for new_index, ep in enumerate(episodes):
        for index, image in enumerate(causal_native_images(ep)):
            if tuple(image.shape) != shape:
                raise ValueError('Source camera shape changes; no implicit resize')
            dataset.add_frame({'observation.state': ep.state[index].astype(np.float32), 'action': ep.action[index].astype(np.float32),
                               camera: image, 'task': ep.language[index]})
        dataset.save_episode(parallel_encoding=False)
        provenance.append({'export_episode_index': new_index, 'source_episode_id': ep.episode_id, 'origin_group': ep.origin_group, 'split': split,
                           'frames': len(ep.timestamps), 'success': ep.success, 'semantics_status': ep.semantics_status})
    dataset.finalize()
    # Official reader acceptance is performed when this optional command is actually run.
    readback = sdk.LeRobotDataset(repo_id=repo_id, root=output, video_backend='pyav')
    expected = sum(len(ep.timestamps) for ep in episodes)
    if len(readback) != expected:
        raise ValueError('Official SDK readback length mismatch')
    for index in (0, expected - 1):
        row = readback[index]
        if tuple(row['action'].shape) != (first.action.shape[1],):
            raise ValueError('Official SDK action shape mismatch')
        if not np.isfinite(row['action'].numpy()).all():
            raise ValueError('Non-finite official SDK batch')
    receipt = {'schema': 'lerobot_export_receipt_v1', 'release_id': manifest['release_id'], 'source_id': source, 'split': split,
               'sdk_commit': SDK_COMMIT, 'sdk_version': importlib.metadata.version('lerobot'), 'codebase_version': readback.meta.info['codebase_version'],
               'normalization': 'native_unnormalized_sdk_owns_statistics', 'camera': camera, 'image_shape': shape, 'video_codec': 'h264', 'encoder_threads': 1, 'frames': expected,
               'episodes': provenance, 'official_reader_first_last_checked': True, 'deployment_ready': False,
               'limitations': ['one camera', 'no depth/force/IMU in this export', 'no physical timing verification', 'no robot capability evaluation', 'partial export directory is invalid unless this receipt exists']}
    write_json(output / 'pipeline_export_receipt.json', receipt)
    return receipt
