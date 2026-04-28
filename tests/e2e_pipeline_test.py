"""E2E test: scan → extract all 7 axes → record claim → verify output."""
import json
import sys
import shutil
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.scan import run_scan
from honne_py import extract
from honne_py.record import record_claim

AXES = ["lexicon", "reaction", "workflow", "ritual", "obsession", "antipattern", "signature"]
FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def e2e_workspace(tmp_path, monkeypatch):
    """Set up a workspace with transcript fixtures and HOME isolation.

    scan.py repo scope resolves transcripts via:
      $HOME/.claude/projects/{PWD.replace('/','_').lstrip('-')}/*.jsonl
    We control the slug by setting PWD=/test-project → slug=test-project.
    """
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PWD", "/test-project")

    slug = "test-project"
    projects_dir = tmp_path / ".claude" / "projects" / slug
    projects_dir.mkdir(parents=True)

    src = FIXTURE_DIR / "sample-session-01.jsonl"
    shutil.copy(src, projects_dir / "session-01.jsonl")

    extra = FIXTURE_DIR / "transcripts" / "test-session-1.jsonl"
    if extra.exists():
        shutil.copy(extra, projects_dir / "session-02.jsonl")

    cache_dir = tmp_path / ".honne" / "cache"
    cache_dir.mkdir(parents=True)
    assets_dir = tmp_path / ".honne" / "assets"
    assets_dir.mkdir(parents=True)

    return tmp_path


class TestE2EPipeline:
    def test_scan_produces_scan_json(self, e2e_workspace):
        scan_path = e2e_workspace / ".honne" / "cache" / "scan.json"
        rc = run_scan(
            scope="repo",
            since="2020-01-01T00:00:00Z",
            cache=scan_path,
            base_dir=e2e_workspace / ".honne",
        )
        assert rc == 0
        assert scan_path.exists()
        data = json.loads(scan_path.read_text())
        assert "run_id" in data
        assert "sessions" in data
        assert len(data["sessions"]) >= 1

    def test_all_7_axes_extract_without_error(self, e2e_workspace):
        scan_path = e2e_workspace / ".honne" / "cache" / "scan.json"
        run_scan(
            scope="repo",
            since="2020-01-01T00:00:00Z",
            cache=scan_path,
            base_dir=e2e_workspace / ".honne",
        )

        extractors = {
            "lexicon": extract.extract_lexicon,
            "reaction": extract.extract_reaction,
            "workflow": extract.extract_workflow,
            "ritual": extract.extract_ritual,
            "obsession": extract.extract_obsession,
            "antipattern": extract.extract_antipattern,
            "signature": extract.extract_signature,
        }

        for axis, fn in extractors.items():
            out_path = e2e_workspace / ".honne" / "cache" / f".axis_{axis}.json"
            rc = fn(scan_path, out_path)
            assert rc == 0, f"extract_{axis} returned {rc}"
            assert out_path.exists(), f".axis_{axis}.json not created"
            data = json.loads(out_path.read_text())
            assert "axis" in data, f"axis field missing in {axis} output"
            assert data["axis"] == axis

    def test_all_7_axes_present_in_extract_output(self, e2e_workspace):
        scan_path = e2e_workspace / ".honne" / "cache" / "scan.json"
        run_scan(
            scope="repo",
            since="2020-01-01T00:00:00Z",
            cache=scan_path,
            base_dir=e2e_workspace / ".honne",
        )

        found_axes = set()
        for axis in AXES:
            out_path = e2e_workspace / ".honne" / "cache" / f".axis_{axis}.json"
            extract_fn = getattr(extract, f"extract_{axis}")
            extract_fn(scan_path, out_path)
            if out_path.exists():
                data = json.loads(out_path.read_text())
                found_axes.add(data.get("axis", ""))

        assert found_axes == set(AXES), f"Missing axes: {set(AXES) - found_axes}"

    def test_record_claim_writes_to_claims_jsonl(self, e2e_workspace):
        scan_path = e2e_workspace / ".honne" / "cache" / "scan.json"
        run_scan(
            scope="repo",
            since="2020-01-01T00:00:00Z",
            cache=scan_path,
            base_dir=e2e_workspace / ".honne",
        )

        claims_path = e2e_workspace / ".honne" / "assets" / "claims.jsonl"
        rc = record_claim(
            type_="claim",
            axis="lexicon",
            scope="repo",
            claim="Uses 'ㅇㅇ' 3 times across sessions (highest frequency short form).",
            out_path=claims_path,
            run_id="test-run-001",
        )
        assert rc == 0
        assert claims_path.exists()

        records = [json.loads(l) for l in claims_path.read_text().splitlines() if l.strip()]
        assert len(records) >= 1
        assert records[-1]["axis"] == "lexicon"
        assert records[-1]["type"] == "claim"
        assert records[-1]["scope"] == "repo"
