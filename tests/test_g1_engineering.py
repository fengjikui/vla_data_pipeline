import json
from pathlib import Path
import av
import numpy as np
from PIL import Image
import pytest
from vla_pipeline.dataset import WindowDataset
from vla_pipeline.io import digest, write_json
from vla_pipeline.lerobot_export import causal_native_images, export_plan
from vla_pipeline.pipeline import run, verify_release
from vla_pipeline.quality import assign_split
from vla_pipeline.register import register_local
from vla_pipeline.unitree import import_unitree


def fixture(root, episodes=8):
    capture = root / 'capture'
    groups = {}
    for episode in range(episodes):
        ep = capture / f'episode_{episode:04d}'
        (ep / 'colors').mkdir(parents=True)
        rows = []
        for frame in range(12):
            rel = f'colors/{frame:06d}.png'
            Image.fromarray(np.full((48, 80, 3), episode * 20 + frame, np.uint8)).save(ep / rel)
            rows.append({'idx': frame, 'colors': {'color_0': rel}, 'states': {'left_arm': {'qpos': [episode, frame / 10]}}, 'actions': {'left_arm': {'qpos': [episode + .1, frame / 10 + .2]}}})
        write_json(ep / 'data.json', {'info': {'image': {'fps': 20}}, 'text': {'goal': 'synthetic task'}, 'data': rows})
        # Ensure both splits exist without depending on luck.
        desired = 'validation' if episode == 0 else 'train'
        index = 0
        while assign_split(f'test-session-{episode}-{index}') != desired:
            index += 1
        groups[f'episode_{episode:04d}/data.json'] = f'test-session-{episode}-{index}'
    mapping = {'source': {'id': 'g1_fixture', 'revision': 'v1', 'label': 'synthetic', 'embodiment': 'fake_2d', 'origin_namespace': 'test', 'license': 'test-only', 'environment': 'synthetic', 'collection': 'generated'}, 'camera': 'color_0', 'timing': {'mode': 'nominal_index'}, 'state_fields': [{'path': 'states.left_arm.qpos', 'names': ['fake_a', 'fake_b'], 'unit': 'synthetic'}], 'action_fields': [{'path': 'actions.left_arm.qpos', 'names': ['fake_a', 'fake_b'], 'unit': 'synthetic'}], 'action_contract': {'type': 'synthetic_target'}, 'origin_groups': groups}
    write_json(root / 'mapping.json', mapping)
    return capture, root / 'mapping.json'


def prepare(root):
    capture, mapping = fixture(root)
    receipt = import_unitree(capture, mapping, root / 'prepared')
    lock = root / 'lock.json'; store = root / 'store'
    register_local(root / 'prepared', root / 'prepared/source.json', store, lock)
    manifest, _ = run(lock, store, offline=True)
    release = store / 'releases' / manifest['release_id']
    return capture, receipt, store, lock, manifest, release


def test_xr_preservation_provenance_full_frame_and_training_windows(tmp_path):
    capture, receipt, store, lock, manifest, release = prepare(tmp_path)
    assert manifest['accepted_episodes'] == 8 and manifest['numeric_frames'] == 96
    for item in receipt['original_files']:
        assert digest(capture / item['path'].removeprefix('original/')) == item['sha256']
        assert digest(tmp_path / 'prepared' / item['path']) == item['sha256']
    q = json.loads((release / 'quality.json').read_text())
    assert all(r['state_names'] == ['fake_a', 'fake_b'] for r in q['episodes'])
    assert all('NOT_measured' in r['source_extras']['timestamp_basis'] for r in q['episodes'])
    assert all(not r['quality']['deployment_ready'] for r in q['episodes'])
    ds = WindowDataset(release, 'g1_fixture')
    row = ds[0]
    assert row['image'].shape == (3, 64, 64) and row['state'].dtype == np.float32
    assert row['actions'].shape == (8, 2) and row['action_mask'].dtype == bool
    canonical = json.loads((release / 'quality.json').read_text())
    assert len(ds) == sum(r['anchors'] for r in canonical['episodes'] if r['split'] == 'train')
    for i in range(len(ds)):
        ds[i]
    assert len(ds.cache) == 1
    assert np.array_equal(ds[-1]['actions'], ds[len(ds) - 1]['actions'])
    with pytest.raises(IndexError):
        ds[len(ds)]
    _, episodes = export_plan(release, store / 'raw', 'g1_fixture', 'train')
    assert len(episodes) == 7
    frames = list(causal_native_images(episodes[0]))
    assert len(frames) == 12 and frames[0].shape == (48, 80, 3)
    # Denormalization must agree with the canonical original action at each valid time.
    import pyarrow.parquet as pq
    train_rec = next(r for r in q['episodes'] if r['split'] == 'train')
    raw = pq.read_table(release / 'canonical/g1_fixture' / (train_rec['episode_id'] + '.parquet')).to_pylist()
    with np.load(release / 'views/g1_fixture/train' / (train_rec['episode_id'] + '.npz')) as arr:
        restored = ds.denormalize_action(arr['actions'][0])
        assert np.allclose(restored, [r['action'] for r in raw[:8]], atol=1e-6)
    again, cached = run(lock, store, True)
    assert cached and again == manifest
    verify_release(release)


@pytest.mark.parametrize('fault', ['dimension', 'idx_gap', 'missing_image', 'path_escape', 'no_goal', 'irregular_time', 'verified_claim'])
def test_xr_import_refuses_ambiguous_or_broken_capture(tmp_path, fault):
    capture, path = fixture(tmp_path, episodes=1)
    mapping = json.loads(path.read_text())
    epfile = capture / 'episode_0000/data.json'; ep = json.loads(epfile.read_text())
    if fault == 'dimension': ep['data'][0]['actions']['left_arm']['qpos'] = [1]
    elif fault == 'idx_gap': ep['data'][2]['idx'] = 100
    elif fault == 'missing_image': ep['data'][0]['colors']['color_0'] = 'absent.png'
    elif fault == 'path_escape': ep['data'][0]['colors']['color_0'] = '../outside.png'
    elif fault == 'no_goal': ep['text']['goal'] = ''
    elif fault == 'irregular_time':
        mapping['timing'] = {'mode': 'measured_timestamp', 'path': 'timestamp_ns', 'scale_to_seconds': 1e-9, 'clock_id': 'monotonic_capture'}
        for i, row in enumerate(ep['data']): row['timestamp_ns'] = i * 50_000_000 + (1_000_000 if i == 2 else 0)
    elif fault == 'verified_claim': mapping['source']['semantics_status'] = 'verified'
    write_json(epfile, ep); write_json(path, mapping)
    with pytest.raises((ValueError, FileNotFoundError)):
        import_unitree(capture, path, tmp_path / 'prepared')
    assert not (tmp_path / 'prepared').exists()


def test_raw_mutation_blocks_optional_sdk_export_preflight(tmp_path):
    _, _, store, _, _, release = prepare(tmp_path)
    original = next((store / 'raw/g1_fixture/v1/original').rglob('*.png'))
    original.write_bytes(b'changed')
    with pytest.raises(ValueError, match='Raw source changed'):
        export_plan(release, store / 'raw', 'g1_fixture', 'train')


def test_recipe_and_contract_change_create_or_quarantine_without_overwrite(tmp_path):
    _, _, store, lock, first, old_release = prepare(tmp_path)
    second, _ = run(lock, store, True, {'horizon': 3, 'anchor_stride': 2})
    assert second['release_id'] != first['release_id']
    with np.load(next((store / 'releases' / second['release_id'] / 'views').rglob('*.npz'))) as row:
        assert row['actions'].shape[1] == 3
    verify_release(old_release)
    # Missing names must be isolated, rather than fitting statistics across different dimensions.
    prepared = tmp_path / 'prepared'; descriptor = json.loads((prepared / 'source.json').read_text())
    epfile = prepared / descriptor['episode_files'][1]; obj = json.loads(epfile.read_text())
    for row in obj['steps']: row['state'].append(99.)
    write_json(epfile, obj); descriptor['revision'] = 'v2'; write_json(prepared / 'source.json', descriptor)
    register_local(prepared, prepared / 'source.json', store, lock)
    third, _ = run(lock, store, True)
    assert third['quarantined_episodes'] == 1

@pytest.mark.parametrize('override', [{'normalize': 'anything'}, {'action_rate': 'resample_30'}, {'pts_roundoff_tolerance_seconds': .5}, {'split_seed': ''}])
def test_unsupported_recipe_never_publishes(tmp_path, override):
    from vla_pipeline.io import write_json
    write_json(tmp_path / 'lock.json', {'sources': []})
    with pytest.raises(ValueError):
        run(tmp_path / 'lock.json', tmp_path / 'store', True, override)
    assert not (tmp_path / 'store/latest.json').exists()

@pytest.mark.parametrize('revision', ['.', '..', 'v1.'])
def test_source_revision_is_portable_and_confined(revision):
    from vla_pipeline.pipeline import validate_lock
    with pytest.raises(ValueError):
        validate_lock({'sources': [{'id': 'g1', 'revision': revision, 'license': 'test', 'origin_namespace': 'test', 'files': []}]})


def test_registered_batch_metadata_cannot_change_in_place(tmp_path):
    capture, mapping = fixture(tmp_path, episodes=1)
    import_unitree(capture, mapping, tmp_path / 'prepared')
    descriptor = tmp_path / 'prepared/source.json'
    register_local(tmp_path / 'prepared', descriptor, tmp_path / 'store', tmp_path / 'lock.json')
    obj = json.loads(descriptor.read_text()); obj['label'] = 'new description'
    write_json(descriptor, obj)
    with pytest.raises(ValueError, match='new revision'):
        register_local(tmp_path / 'prepared', descriptor, tmp_path / 'store', tmp_path / 'lock.json')


def test_unlocked_media_cannot_enter_release(tmp_path):
    _, _, store, lock, _, _ = prepare(tmp_path)
    obj = json.loads(lock.read_text())
    media = next(f for f in obj['sources'][0]['files'] if f['path'].endswith('.mp4'))
    obj['sources'][0]['files'].remove(media)
    write_json(lock, obj)
    result, _ = run(lock, store, True)
    assert result['accepted_episodes'] == 7 and result['quarantined_episodes'] == 1
    q = json.loads((store / 'releases' / result['release_id'] / 'quality.json').read_text())
    assert 'source lock' in q['quarantined'][0]['reason']
