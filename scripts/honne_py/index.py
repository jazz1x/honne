from typing import Union, Optional, List, Iterator
import json
from pathlib import Path


def index_session(jsonl_path: Union[Path, str], out_path: Union[Path, str]) -> int:
    """Index a single JSONL session file."""
    jsonl_path, out_path = Path(jsonl_path), Path(out_path)

    messages = []
    try:
        with open(jsonl_path) as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                if obj.get("message", {}).get("role"):
                    messages.append({
                        "role": obj["message"]["role"],
                        "text": obj["message"].get("content", "")[:100],
                    })
    except Exception:
        return 1

    result = {
        "session_id": "",
        "message_count": len(messages),
        "preview": messages[:3],
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonl", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    exit(index_session(args.jsonl, args.out))
