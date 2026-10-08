"""Show exactly what a model receives, without loading a pretrained model."""
import argparse
import json
from pathlib import Path
import numpy as np
from vla_pipeline.dataset import WindowDataset


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--release', type=Path, required=True)
    p.add_argument('--source', required=True)
    p.add_argument('--split', default='train', choices=['train', 'validation'])
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    dataset = WindowDataset(args.release, args.source, args.split)
    if not len(dataset):
        raise ValueError('Selected split has no training windows')
    row = dataset[0]
    summary = {'release_id': dataset.release_id, 'samples': len(dataset), 'split': args.split,
               'fields': {k: {'shape': list(v.shape), 'dtype': str(v.dtype)} if isinstance(v, np.ndarray) else v for k, v in row.items()},
               'valid_action_elements': int(row['action_mask'].sum()), 'deployment_ready': False}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if args.output:
        from vla_pipeline.io import write_json
        write_json(args.output, summary)

if __name__ == '__main__':
    main()
