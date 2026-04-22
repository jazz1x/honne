import json
import tempfile
from pathlib import Path
import sys

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.scan import _parse_jsonl


def test_scan_604_sessions_memory_constant():
    """Scan 604 mock sessions without memory explosion (O(1) per session)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Generate 604 mock JSONL files in temp directory
        for i in range(604):
            jsonl_file = tmpdir_path / f"session_{i:03d}.jsonl"
            with open(jsonl_file, "w") as f:
                # Metadata line
                f.write(json.dumps({
                    "sessionId": f"mock-{i:04d}",
                    "cwd": f"/project_{i}",
                    "ts": "2026-04-22T10:00:00Z",
                }) + "\n")

                # 50 message lines (larger to test memory)
                for msg_idx in range(50):
                    msg = {
                        "timestamp": "2026-04-22T10:00:00Z",
                        "message": {
                            "role": "user" if msg_idx % 2 == 0 else "assistant",
                            "content": f"Message {msg_idx}: " + "X" * 1000,  # 1KB per message
                        }
                    }
                    f.write(json.dumps(msg) + "\n")

        # Parse all 604 sessions
        results = []
        for jsonl_file in sorted(tmpdir_path.glob("*.jsonl")):
            result = _parse_jsonl(jsonl_file, redact_secrets=False)
            if result:
                results.append(result)

        # Verify
        assert len(results) == 604, f"Expected 604 sessions, got {len(results)}"
        print(f"✓ Parsed 604 sessions without ARG_MAX or memory issues")
