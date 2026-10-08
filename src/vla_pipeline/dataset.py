"""Bounded-memory training view reader; no Torch dependency in base install."""
from collections import OrderedDict
import json
from pathlib import Path
import numpy as np
from .pipeline import verify_release


class WindowDataset:
    """Map-style Dataset accepted by torch.utils.data.DataLoader.

    Each cached NPZ contains one episode's anchors, never an entire source.
    Use num_workers=0 for the manual CPU demonstration. Production large shards
    need a different storage backend; compressed NPZ is not a memory map.
    """
    def __init__(self, release, source, split='train', cache_episodes=1):
        self.release = Path(release)
        manifest = verify_release(self.release)
        if source not in {s['id'] for s in manifest['sources']}:
            raise ValueError('Unknown source')
        if split not in ('train', 'validation') or cache_episodes < 1:
            raise ValueError('Invalid split/cache size')
        self.statistics = json.loads((self.release / 'statistics.json').read_text(encoding='utf-8'))[source]
        self.release_id = manifest['release_id']
        self.files = sorted((self.release / 'views' / source / split).glob('*.npz'))
        self.ends = []
        for path in self.files:
            with np.load(path, allow_pickle=False) as batch:
                n = len(batch['anchor_index'])
            self.ends.append(n + (self.ends[-1] if self.ends else 0))
        self.cache = OrderedDict()
        self.cache_episodes = cache_episodes

    def __len__(self):
        return self.ends[-1] if self.ends else 0

    def __getitem__(self, index):
        if index < 0:
            index += len(self)
        if not 0 <= index < len(self):
            raise IndexError(index)
        file_index = int(np.searchsorted(self.ends, index, side='right'))
        offset = index - (self.ends[file_index - 1] if file_index else 0)
        path = self.files[file_index]
        if path not in self.cache:
            with np.load(path, allow_pickle=False) as arrays:
                self.cache[path] = {k: arrays[k] for k in arrays.files}
            if len(self.cache) > self.cache_episodes:
                self.cache.popitem(last=False)
        self.cache.move_to_end(path)
        batch = self.cache[path]
        return {'image': np.transpose(batch['image'][offset].astype(np.float32) / 255, (2, 0, 1)),
                'state': batch['state'][offset].copy(), 'actions': batch['actions'][offset].copy(),
                'action_mask': batch['action_mask'][offset].copy(), 'language': str(batch['language'][offset]),
                'timestamp': float(batch['timestamp'][offset]), 'anchor_index': int(batch['anchor_index'][offset])}

    def denormalize_action(self, actions):
        return np.asarray(actions) * np.asarray(self.statistics['action']['std']) + np.asarray(self.statistics['action']['mean'])
