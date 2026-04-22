from typing import Union, Optional, List, Iterator
import json
from datetime import datetime
from pathlib import Path


def query(
    base_dir: Union[Path, str],
    scope: str = "repo",
    since: str = None,
    until: str = None,
    tag: str = None,
    tags: str = None,
    type_: str = None,
    types: str = None,
    out_path: Union[Path, str] = None,
) -> int:
    """Query assets with filters."""
    base_dir = Path(base_dir) if base_dir else Path.cwd() / ".harnish"

    # Load assets from .harnish directory
    result = []
    asset_dir = base_dir / "assets"
    if asset_dir.exists():
        for asset_file in asset_dir.glob("*.jsonl"):
            with open(asset_file) as f:
                for line in f:
                    if not line.strip():
                        continue
                    obj = json.loads(line)

                    # Apply filters
                    if type_ and obj.get("type") != type_:
                        continue
                    if since and obj.get("created_at", "") < since:
                        continue
                    if until and obj.get("created_at", "") > until:
                        continue

                    result.append(obj)

    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f)

    return 0 if result else 2


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir")
    parser.add_argument("--scope")
    parser.add_argument("--since")
    parser.add_argument("--until")
    parser.add_argument("--tag")
    parser.add_argument("--tags")
    parser.add_argument("--type")
    parser.add_argument("--types")
    parser.add_argument("--out")
    args = parser.parse_args()
    exit(query(
        args.base_dir,
        args.scope,
        args.since,
        args.until,
        args.tag,
        args.tags,
        args.type,
        args.types,
        args.out,
    ))
