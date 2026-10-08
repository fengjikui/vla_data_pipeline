"""Explicit, offline XR JSON/image import. This is not a robot controller.

A mapping selects fields; no G1 joint order, hand type, units or real timing is
inferred from a product name. The original capture is preserved byte for byte.
"""
from __future__ import annotations
from fractions import Fraction
import json
import os
from pathlib import Path
import shutil
import tempfile
import av
import numpy as np
from PIL import Image
from .io import confined, digest, object_hash, write_json


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def get_field(row, dotted):
    for part in dotted.split('.'):
        row = row[part]
    return row


def flatten(row, fields):
    values = []
    for field in fields:
        arr = np.asarray(get_field(row, field['path']), dtype=np.float64).reshape(-1)
        if len(arr) != len(field['names']) or not np.isfinite(arr).all():
            raise ValueError('Field dimension or finite-value mismatch: ' + field['path'])
        values.extend(arr.tolist())
    return values


def validate_mapping(mapping):
    source = mapping['source']
    required = ('id', 'revision', 'embodiment', 'origin_namespace', 'license', 'environment', 'collection')
    if any(not source.get(key) for key in required):
        raise ValueError('Mapping requires source identity, rights and provenance')
    if source.get('semantics_status', 'unknown') != 'unknown':
        raise ValueError('XR import records declared semantics only; deployment verification is a separate gate')
    for key in ('state_fields', 'action_fields'):
        fields = mapping[key]
        if not fields or any(not f.get('path') or not f.get('names') or not f.get('unit') for f in fields):
            raise ValueError('Explicit field paths, names and units required: ' + key)
        names = [name for f in fields for name in f['names']]
        if any(not isinstance(n, str) or not n for n in names) or len(names) != len(set(names)):
            raise ValueError('Field names must be unique nonempty strings')
    if not mapping.get('camera') or not mapping.get('action_contract'):
        raise ValueError('Camera and action_contract required')
    if mapping['timing']['mode'] not in ('nominal_index', 'measured_timestamp'):
        raise ValueError('Unsupported timing mode')


def _timestamps(rows, fps, timing):
    if timing['mode'] == 'nominal_index':
        # A sparse idx sequence indicates dropped records, not a faster video.
        indices = [r['idx'] for r in rows]
        if indices != list(range(indices[0], indices[0] + len(rows))):
            raise ValueError('Non-contiguous XR idx; timing repair must be explicit')
        times = np.arange(len(rows), dtype=np.float64) / fps
        basis = 'nominal_idx_over_fps_NOT_measured_hardware_time'
    else:
        times = np.asarray([get_field(r, timing['path']) for r in rows], dtype=np.float64)
        times *= float(timing['scale_to_seconds'])
        times -= times[0]
        basis = 'measured_field_rebased_to_episode_seconds'
        if not timing.get('clock_id'):
            raise ValueError('Measured timestamp requires clock_id')
    if not np.isfinite(times).all() or np.any(np.diff(times) <= 0):
        raise ValueError('Non-finite or non-monotonic timestamps')
    if not np.allclose(times, np.arange(len(rows)) / fps, atol=1e-6, rtol=0):
        raise ValueError('Irregular timing: this importer refuses implicit resampling')
    return times, basis


def encode_images(paths, output, fps):
    """Small sequential encoder, with explicit PTS and one codec thread."""
    with Image.open(paths[0]) as image:
        width, height = image.size
    if width % 2 or height % 2:
        raise ValueError('Video dimensions must be even; crop/resize belongs in an explicit recipe')
    with av.open(str(output), 'w') as container:
        stream = container.add_stream('mpeg4', rate=Fraction(str(fps)).limit_denominator(100000))
        stream.width, stream.height = width, height
        stream.pix_fmt = 'yuv420p'
        stream.codec_context.thread_count = 1
        stream.options = {'qscale': '2'}
        for index, path in enumerate(paths):
            with Image.open(path) as image:
                if image.size != (width, height):
                    raise ValueError('Image size changes inside episode')
                rgb = np.asarray(image.convert('RGB'))
            frame = av.VideoFrame.from_ndarray(rgb, format='rgb24')
            frame.pts = index
            frame.time_base = 1 / Fraction(str(fps)).limit_denominator(100000)
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return [height, width, 3]


def import_unitree(source_dir, mapping_path, output):
    source_dir, output = Path(source_dir).resolve(), Path(output).resolve()
    mapping = read_json(mapping_path)
    validate_mapping(mapping)
    if output.exists():
        raise FileExistsError('Converted batch already exists; use a new output/revision')
    if output.is_relative_to(source_dir) or source_dir.is_relative_to(output):
        raise ValueError('Source and output trees must be separate')
    episode_files = mapping.get('episode_files') or [p.relative_to(source_dir).as_posix() for p in sorted(source_dir.rglob('data.json'))]
    if not episode_files:
        raise ValueError('No XR data.json episodes found')
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.importing-', dir=output.parent))
    try:
        # Store every original modality, not just the camera/action view selected below.
        originals = []
        for path in sorted(source_dir.rglob('*')):
            if path.is_symlink():
                raise ValueError('Capture tree may not contain symlinks')
            if not path.is_file():
                continue
            rel = path.relative_to(source_dir).as_posix()
            target = confined(stage / 'original', rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            originals.append({'path': 'original/' + rel, 'bytes': target.stat().st_size, 'sha256': digest(target)})
        write_json(stage / 'mapping.json', mapping)
        descriptor = dict(mapping['source'], format='lab_json_v1', semantics_status='unknown', episode_files=[], extra_files=[x['path'] for x in originals] + ['mapping.json', 'conversion.json'])
        descriptor['state_names'] = [n for f in mapping['state_fields'] for n in f['names']]
        descriptor['action_names'] = [n for f in mapping['action_fields'] for n in f['names']]
        descriptor['action_contract'] = mapping['action_contract']
        receipt = {'schema': 'unitree_import_receipt_v1', 'mapping_sha256': digest(stage / 'mapping.json'), 'original_files': originals, 'episodes': [], 'codec': 'mpeg4_lossy_original_images_preserved', 'codec_threads': 1, 'deployment_ready': False}
        for rel in episode_files:
            # Read the copied snapshot, so later changes in incoming cannot change conversion.
            data_path = confined(stage / 'original', rel)
            native = read_json(data_path)
            rows = native['data']
            if len(rows) < 2:
                raise ValueError('Episode needs at least two records: ' + rel)
            fps = float(mapping['fps'] if 'fps' in mapping else native['info']['image']['fps'])
            if not np.isfinite(fps) or fps <= 0:
                raise ValueError('Invalid capture frequency')
            timestamps, basis = _timestamps(rows, fps, mapping['timing'])
            goal = native.get('text', {}).get('goal')
            if not isinstance(goal, str) or not goal.strip():
                raise ValueError('Task goal missing; do not fabricate instruction')
            state = [flatten(row, mapping['state_fields']) for row in rows]
            action = [flatten(row, mapping['action_fields']) for row in rows]
            image_paths = [confined(data_path.parent, r['colors'][mapping['camera']]) for r in rows]
            eid = 'xr_' + object_hash({'path': rel})[:16]
            video_rel = 'media/' + eid + '.mp4'
            (stage / 'media').mkdir(exist_ok=True)
            shape = encode_images(image_paths, stage / video_rel, fps)
            # Explicit session grouping is recommended; default episode grouping is only an engineering holdout.
            group = mapping.get('origin_groups', {}).get(rel, mapping['source']['origin_namespace'] + ':' + rel)
            result = native.get('result')
            success = mapping.get('result_map', {}).get(str(result)) if result is not None else None
            if success is not None and not isinstance(success, bool):
                raise ValueError('result_map values must be booleans')
            ep = {'episode_id': eid, 'origin_group': group, 'fps': fps, 'video': video_rel, 'success': success, 'timestamp_basis': basis,
                  'alignment_assumption': 'image and qpos from same saved record; acquisition latency and availability NOT measured',
                  'provenance': {'original_json': 'original/' + rel, 'mapping_sha256': receipt['mapping_sha256'], 'native_result': result},
                  'steps': [{'timestamp': float(t), 'state': s, 'action': a, 'language': goal} for t, s, a in zip(timestamps, state, action)]}
            ep_rel = 'episodes/' + eid + '.json'
            write_json(stage / ep_rel, ep)
            descriptor['episode_files'].append(ep_rel)
            receipt['episodes'].append({'episode_id': eid, 'original_json': 'original/' + rel, 'records': len(rows), 'fps': fps, 'image_shape': shape, 'timestamp_basis': basis, 'success': success, 'origin_group': group})
        write_json(stage / 'conversion.json', receipt)
        write_json(stage / 'source.json', descriptor)
        os.rename(stage, output)
        return receipt
    finally:
        if stage.exists():
            shutil.rmtree(stage)
