"""Deterministic JSON, bounded downloads, and path confinement."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def object_hash(value) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + '\n'
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.writing-')
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(payload)
        os.replace(temp, path)
    finally:
        Path(temp).unlink(missing_ok=True)


def confined(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path outside source root: {relative}')
    return path


def fetch(url: str, path: Path, max_bytes: int, expected_sha256: str | None = None, offline=False) -> dict:
    if path.exists():
        if path.stat().st_size > max_bytes:
            raise ValueError('Cached file exceeds byte limit')
        sha = digest(path)
        if expected_sha256 and sha != expected_sha256:
            raise ValueError(f'Hash mismatch in cache: {path}')
        return {'bytes': path.stat().st_size, 'sha256': sha}
    if offline:
        raise FileNotFoundError(f'Offline cache missing: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix='.download-')
    try:
        with urllib.request.urlopen(url, timeout=60) as response, os.fdopen(fd, 'wb') as f:
            n = 0
            while chunk := response.read(1024 * 1024):
                n += len(chunk)
                if n > max_bytes:
                    raise ValueError(f'Download exceeds limit: {url}')
                f.write(chunk)
        sha = digest(Path(temp))
        if expected_sha256 and sha != expected_sha256:
            raise ValueError(f'Download hash mismatch: {url}')
        os.replace(temp, path)
        return {'bytes': n, 'sha256': sha}
    finally:
        Path(temp).unlink(missing_ok=True)
