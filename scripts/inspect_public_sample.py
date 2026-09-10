"""Inspect one pinned, CC-BY-4.0 NVIDIA G1 numeric episode; no robot control.

Run: uv run --with pyarrow==25.0.1 python scripts/inspect_public_sample.py
Only small Parquet/JSON files are fetched; videos and full datasets are excluded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import tempfile
import urllib.request

import pyarrow.parquet as pq


REPO = "nvidia/PhysicalAI-Robotics-GR00T-Teleop-G1"
REVISION = "0d7bdd06e67f3ca0868892d0ec8f03bcd3e49e40"
EPISODE = "g1-pick-apple/data/chunk-000/episode_000000.parquet"
EXPECTED_SHA256 = "a0d5b462c5d27a7378b4bef68cbd6fdfcd85c5c033f5e9bd2abca47fe67fa22d"
MAX_FILE_BYTES = 2 * 1024 * 1024


def url_for(relative_path: str) -> str:
    return f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{relative_path}"


def fetch_small_file(relative_path: str, cache_dir: Path) -> Path:
    destination = cache_dir / relative_path
    if destination.exists():
        if destination.stat().st_size > MAX_FILE_BYTES:
            raise ValueError(f"Cached file exceeds size limit: {destination}")
        return destination
    with urllib.request.urlopen(url_for(relative_path), timeout=30) as response:
        payload = response.read(MAX_FILE_BYTES + 1)
    if len(payload) > MAX_FILE_BYTES:
        raise ValueError(f"Refusing unexpectedly large sample: {relative_path}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    return destination


def inspect(cache_dir: Path) -> dict:
    parquet_path = fetch_small_file(EPISODE, cache_dir)
    digest = hashlib.sha256(parquet_path.read_bytes()).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("Sample hash differs from the research record; inspect the cache/source.")
    info_path = fetch_small_file("g1-pick-apple/meta/info.json", cache_dir)
    tasks_path = fetch_small_file("g1-pick-apple/meta/tasks.jsonl", cache_dir)
    info = json.loads(info_path.read_text())
    tasks = {item["task_index"]: item["task"] for item in
             (json.loads(line) for line in tasks_path.read_text().splitlines() if line.strip())}
    table = pq.read_table(parquet_path)
    rows = table.to_pylist()
    if len(rows) < 2:
        raise ValueError("At least two rows are required to inspect timing.")
    for row in rows:
        for field in ("observation.state", "action"):
            if len(row[field]) != info["features"][field]["shape"][0]:
                raise ValueError(f"Shape mismatch: {field}")
            if not all(math.isfinite(value) for value in row[field]):
                raise ValueError(f"Non-finite numeric value: {field}")
        if row["task_index"] not in tasks:
            raise ValueError("Task reference is unresolved.")
    times = [row["timestamp"] for row in rows]
    if not all(math.isfinite(t) for t in times):
        raise ValueError("Non-finite timestamp.")
    if not all(b > a for a, b in zip(times, times[1:])):
        raise ValueError("Timestamps are not strictly increasing.")
    if len({row["episode_index"] for row in rows}) != 1:
        raise ValueError("This pinned v2 sample should contain one episode.")
    return {
        "source_url": url_for(EPISODE),
        "source_repo": REPO,
        "revision": REVISION,
        "license": "CC-BY-4.0",
        "attribution": "NVIDIA GEAR, PhysicalAI-Robotics-GR00T-Teleop-G1",
        "inspection_scope": "One numeric episode; metadata and task lookup; no video decoding or training.",
        "sha256": digest,
        "bytes": parquet_path.stat().st_size,
        "rows": table.num_rows,
        "columns": table.column_names,
        "subset_metadata": {
            key: info[key] for key in ("codebase_version", "fps", "total_episodes", "total_frames")
        },
        "task": tasks[rows[0]["task_index"]],
        "first_two_rows": rows[:2],
        "checks": {
            "all_numeric_values_finite": True,
            "all_timestamps_strictly_increasing": True,
            "single_episode": True,
            "state_dim": len(rows[0]["observation.state"]),
            "action_dim": len(rows[0]["action"]),
            "timestamp_delta": times[1] - times[0],
            "last_timestamp": times[-1],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path,
                        default=Path(tempfile.gettempdir()) / "vla-g1-pinned-sample" / REVISION)
    parser.add_argument("--output", type=Path, help="Optional JSON inspection report path")
    args = parser.parse_args()
    result = inspect(args.cache_dir)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    summary = {key: value for key, value in result.items() if key != "first_two_rows"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
