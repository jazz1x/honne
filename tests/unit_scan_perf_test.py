import json
import time
from pathlib import Path
import sys
import os

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.scan import _parse_jsonl


def test_scan_100_fixtures_under_5sec():
    """100 fixture scan should complete < 5 seconds."""
    fixtures_dir = Path(__file__).parent / "fixtures" / "scan_perf"

    # Verify fixtures exist
    fixture_files = sorted(fixtures_dir.glob("*.jsonl"))
    assert len(fixture_files) == 100, f"Expected 100 fixtures, got {len(fixture_files)}"

    start = time.monotonic()

    # Parse all fixtures
    results = []
    for fixture_file in fixture_files:
        result = _parse_jsonl(fixture_file, redact_secrets=False)
        if result:
            results.append(result)

    elapsed = time.monotonic() - start

    # Verify results
    assert len(results) > 0, "No sessions parsed"
    assert elapsed < 5.0, f"Scan took {elapsed:.2f}s, expected < 5s"

    print(f"✓ Parsed {len(results)} sessions in {elapsed:.2f}s")
