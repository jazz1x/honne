from typing import Union
import json
import sys
from pathlib import Path


def query(
    base_dir: Union[Path, str],
    scope: str = None,
    since: str = None,
    until: str = None,
    tag: str = None,
    tags: str = None,
    type_: str = None,
    types: str = None,
    out_path: Union[Path, str] = None,
) -> int:
    """Query assets with filters."""
    base_dir = Path(base_dir) if base_dir else Path.cwd() / ".honne"

    # Load assets from base_dir/.honne directory
    result = []
    asset_dir = base_dir / "assets"

    # Graceful fallback: missing base_dir or assets dir
    if not base_dir.exists():
        print(json.dumps([]))
        return 0
    if not asset_dir.exists():
        print(json.dumps([]))
        return 0

    # Type to file mapping
    type_to_file = {
        "claim": "claims.jsonl",
        "rejection": "rejections.jsonl",
        "evolution": "evolutions.jsonl",
    }
    target_file = asset_dir / type_to_file.get(type_, "claims.jsonl")

    if not target_file.exists():
        print(json.dumps([]))
        return 0

    # Load and filter
    try:
        with open(target_file) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    sys.stderr.write(f"warning: skipping malformed line\n")
                    continue

                # Apply filters (type is already partitioned by target_file)
                if since and obj.get("created_at", "") < since:
                    continue
                if until and obj.get("created_at", "") > until:
                    continue
                if scope is not None and obj.get("scope") != scope:
                    continue
                if tag is not None and obj.get("axis") != tag:
                    continue
                if tags is not None:
                    tag_list = [t.strip() for t in tags.split(",")]
                    if obj.get("axis") not in tag_list:
                        continue

                result.append(obj)
    except Exception as e:
        sys.stderr.write(f"error: {e}\n")
        return 1

    print(json.dumps(result))

    if out_path:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f)

    return 0


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
