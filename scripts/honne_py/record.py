from typing import Optional, Union
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def record_claim(
    type_: str,
    axis: str,
    scope: str,
    claim: str,
    out_path: Union[Path, str],
    support_count: int = 1,
    prior_id: str = None,
    quotes_json: str = None,
    run_id: Optional[str] = None,
    quotes_file: Optional[str] = None,
) -> int:
    """Record a claim to JSONL."""
    out_path = Path(out_path)

    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    claim_id = hashlib.sha256(
        f"{type_}:{axis}:{claim}:{run_id or ''}:{created_at}".encode()
    ).hexdigest()[:16]

    if quotes_file:
        try:
            with open(quotes_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            if isinstance(raw, dict):
                quotes = raw.get("quotes", [])
                if "quotes" not in raw:
                    print(f"warn: quotes file {quotes_file} has no 'quotes' key, defaulting to empty", file=sys.stderr)
            else:
                quotes = raw
        except (FileNotFoundError, json.JSONDecodeError, OSError) as e:
            print(f"error: failed to read quotes file {quotes_file}: {e}", file=sys.stderr)
            return 1
    elif quotes_json:
        try:
            quotes = json.loads(quotes_json)
        except json.JSONDecodeError as e:
            print(f"error: malformed --quotes-json: {e}", file=sys.stderr)
            return 1
    else:
        quotes = []

    record = {
        "id": claim_id,
        "type": type_,
        "axis": axis,
        "scope": scope,
        "run_id": run_id,
        "claim": claim,
        "support_count": support_count,
        "prior_id": prior_id,
        "quotes": quotes,
        "created_at": created_at,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "a") as f:
        f.write(json.dumps(record) + "\n")

    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True)
    parser.add_argument("--axis", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--claim", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--support-count", type=int, default=1)
    parser.add_argument("--prior-id")
    parser.add_argument("--quotes-json")
    parser.add_argument("--quotes-file")
    parser.add_argument("--run-id")
    args = parser.parse_args()
    exit(record_claim(
        type_=args.type,
        axis=args.axis,
        scope=args.scope,
        claim=args.claim,
        out_path=args.out,
        support_count=args.support_count,
        prior_id=args.prior_id,
        quotes_json=args.quotes_json,
        run_id=args.run_id,
        quotes_file=args.quotes_file,
    ))
