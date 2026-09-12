"""Register self-collected files without overwriting an earlier raw revision."""
from pathlib import Path
import json
import shutil
from .io import confined,digest,write_json
from .pipeline import validate_lock


def register_local(source_dir,descriptor,root,output):
    source_dir=Path(source_dir).resolve()
    spec=json.loads(Path(descriptor).read_text())
    if spec['format']!='lab_json_v1':raise ValueError('Local registration currently accepts lab_json_v1')
    spec['files']=[]
    validate_lock({'sources':[spec]})
    paths=set(spec['episode_files'])
    for rel in spec['episode_files']:
        item=json.loads(confined(source_dir,rel).read_text())
        if item.get('video'):paths.add(item['video'])
    for rel in sorted(paths):
        path=confined(source_dir,rel)
        spec['files'].append({'path':rel,'bytes':path.stat().st_size,'sha256':digest(path)})
    validate_lock({'sources':[spec]})
    # Verify all collisions before copying any files.
    for f in spec['files']:
        dest=confined(Path(root)/'raw'/spec['id']/spec['revision'],f['path'])
        if dest.exists() and digest(dest)!=f['sha256']:raise ValueError('Raw revision already exists with different bytes; assign a new revision')
    for f in spec['files']:
        dest=confined(Path(root)/'raw'/spec['id']/spec['revision'],f['path']);dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():shutil.copy2(confined(source_dir,f['path']),dest)
    lock={'schema_version':'1.0','sources':[spec]};write_json(Path(output),lock)
    return lock
