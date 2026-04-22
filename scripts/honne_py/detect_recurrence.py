from typing import Union, Optional, List, Iterator
import json
from datetime import datetime
from pathlib import Path


def detect(input_path: Union[Path, str], out_path: Union[Path, str], min_sessions: int = 3) -> int:
    """Detect recurrence: concepts that appear in min_sessions+ sessions."""
    input_path, out_path = Path(input_path), Path(out_path)

    try:
        with open(input_path) as f:
            data = json.load(f)
    except Exception:
        return 1

    sessions = data.get("sessions", [])
    if not sessions:
        return 2

    # Build concept → session map
    concepts = {}
    for session in sessions:
        session_id = session.get("session_id")
        messages = session.get("messages", [])
        text = " ".join([msg.get("text", "") for msg in messages])

        # Extract 3-grams
        words = text.split()
        for i in range(len(words) - 2):
            concept = " ".join(words[i:i+3])
            if concept not in concepts:
                concepts[concept] = []
            if session_id not in concepts[concept]:
                concepts[concept].append(session_id)

    # Filter by min_sessions
    result = []
    for concept, session_ids in concepts.items():
        if len(session_ids) >= min_sessions:
            result.append({
                "concept": concept,
                "sessions": session_ids,
                "count": len(session_ids),
            })

    # Sort by count
    result.sort(key=lambda x: x["count"], reverse=True)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f)

    return 0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--min-sessions", type=int, default=3)
    args = parser.parse_args()

    exit(detect(args.input, args.out, args.min_sessions))
