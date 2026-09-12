import argparse
import json
from pathlib import Path
from .pipeline import run,verify_release


def main():
    parser=argparse.ArgumentParser(description='VLA data pipeline: engineering prototype, no robot control')
    sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('run');p.add_argument('--lock',type=Path,default=Path('configs/demo_sources.lock.json'));p.add_argument('--root',type=Path,default=Path('data'));p.add_argument('--offline',action='store_true')
    p=sub.add_parser('verify');p.add_argument('release',type=Path)
    p=sub.add_parser('register-local');p.add_argument('--source-dir',type=Path,required=True);p.add_argument('--descriptor',type=Path,required=True);p.add_argument('--root',type=Path,default=Path('data'));p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='run':
        manifest,cached=run(args.lock,args.root,args.offline)
        print(json.dumps({k:v for k,v in manifest.items() if k not in ('output_sha256','recipe')},ensure_ascii=False,indent=2));print('Reused immutable release:',cached)
    elif args.command=='register-local':
        from .register import register_local
        lock=register_local(args.source_dir,args.descriptor,args.root,args.output)
        print('Registered',lock['sources'][0]['id'],'at',args.output)
    else:
        manifest=verify_release(args.release);print('Verified:',manifest['release_id'],len(manifest['output_sha256']),'files')

if __name__=='__main__':main()
