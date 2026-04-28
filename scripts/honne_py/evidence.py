from typing import Union
import json
from pathlib import Path


def gather(input_path: Union[Path, str], claim: str, out_path: Union[Path, str], max_: int = 10) -> int:
    """Gather evidence for a claim."""
    input_path, out_path = Path(input_path), Path(out_path)

    try:
        with open(input_path) as f:
            data = json.load(f)
    except Exception:
        return 1

    sessions = data.get("sessions", [])
    evidence = []

    for session in sessions:
        if len(evidence) >= max_:
            break
        messages = session.get("messages", [])
        for msg in messages:
            text = msg.get("text", "").lower()
            if claim.lower() in text:
                evidence.append({
                    "session_id": session.get("session_id"),
                    "quote": text[:200],
                })
                if len(evidence) >= max_:
                    break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(evidence, f)

    return 0 if evidence else 2


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--claim", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--max", type=int, default=10)
    args = parser.parse_args()
    exit(gather(args.input, args.claim, args.out, args.max))
