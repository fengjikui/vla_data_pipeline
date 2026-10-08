import argparse
import json
from pathlib import Path
from .pipeline import run, verify_release


def main():
    parser = argparse.ArgumentParser(description='Auditable robot data pipeline; no robot control')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('run')
    p.add_argument('--lock', type=Path, default=Path('configs/demo_sources.lock.json'))
    p.add_argument('--root', type=Path, default=Path('data'))
    p.add_argument('--offline', action='store_true')
    p.add_argument('--recipe', type=Path, help='Explicit JSON recipe; changing it creates a new release')
    p = sub.add_parser('verify'); p.add_argument('release', type=Path)
    p = sub.add_parser('register-local')
    p.add_argument('--source-dir', type=Path, required=True); p.add_argument('--descriptor', type=Path, required=True)
    p.add_argument('--root', type=Path, default=Path('data')); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('import-unitree', help='Preserve original XR files and prepare lab_json_v1')
    p.add_argument('--source-dir', type=Path, required=True); p.add_argument('--mapping', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('export-lerobot', help='Optional pinned official SDK bridge; requires separate environment')
    p.add_argument('--release', type=Path, required=True); p.add_argument('--raw-root', type=Path, required=True)
    p.add_argument('--source', required=True); p.add_argument('--split', choices=['train', 'validation'], required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--repo-id', required=True)
    args = parser.parse_args()
    if args.command == 'run':
        recipe = json.loads(args.recipe.read_text(encoding='utf-8')) if args.recipe else None
        manifest, cached = run(args.lock, args.root, args.offline, recipe)
        print(json.dumps({k: v for k, v in manifest.items() if k not in ('output_sha256', 'recipe')}, ensure_ascii=False, indent=2))
        print('Reused immutable release:', cached)
    elif args.command == 'register-local':
        from .register import register_local
        lock = register_local(args.source_dir, args.descriptor, args.root, args.output)
        print('Registered', lock['sources'][0]['id'], 'at', args.output)
    elif args.command == 'import-unitree':
        from .unitree import import_unitree
        receipt = import_unitree(args.source_dir, args.mapping, args.output)
        print('Converted', len(receipt['episodes']), 'episodes; original files preserved; deployment_ready=False')
    elif args.command == 'export-lerobot':
        from .lerobot_export import export_lerobot
        print(json.dumps(export_lerobot(args.release, args.raw_root, args.source, args.split, args.output, args.repo_id), ensure_ascii=False, indent=2))
    else:
        manifest = verify_release(args.release)
        print('Verified:', manifest['release_id'], len(manifest['output_sha256']), 'files')

if __name__ == '__main__':
    main()
