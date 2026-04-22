from typing import Union, Optional, List, Iterator
import hashlib
import json
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
) -> int:
    """Record a claim to JSONL."""
    out_path = Path(out_path)

    # Generate SHA256 ID
    claim_text = f"{type_}:{axis}:{claim}"
    claim_id = hashlib.sha256(claim_text.encode()).hexdigest()[:16]

    record = {
        "id": claim_id,
        "type": type_,
        "axis": axis,
        "scope": scope,
        "claim": claim,
        "support_count": support_count,
        "prior_id": prior_id,
        "quotes": json.loads(quotes_json) if quotes_json else [],
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
    args = parser.parse_args()
    exit(record_claim(
        args.type,
        args.axis,
        args.scope,
        args.claim,
        args.out,
        args.support_count,
        args.prior_id,
        args.quotes_json,
    ))
