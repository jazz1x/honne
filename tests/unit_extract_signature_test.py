"""Unit tests for extract_signature — decisive_close and targeted_request signals."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from honne_py.extract import extract_signature


def _make_scan(messages_by_session: dict, tmp_path: Path) -> Path:
    sessions = [
        {
            "session_id": sid,
            "started_at": "2025-01-01T00:00:00Z",
            "messages": [{"role": role, "text": text} for role, text in msgs],
        }
        for sid, msgs in messages_by_session.items()
    ]
    p = tmp_path / "scan.json"
    p.write_text(json.dumps({"sessions": sessions}))
    return p


class TestDecisiveClose:
    def test_short_ok_counts(self, tmp_path):
        scan = _make_scan({"s1": [("user", "ok")]}, tmp_path)
        out = tmp_path / "sig.json"
        assert extract_signature(scan, out) == 0
        data = json.loads(out.read_text())
        assert data["counters"]["decisive_close"] >= 1

    def test_korean_closure_counts(self, tmp_path):
        scan = _make_scan({"s1": [("user", "네"), ("user", "좋아"), ("user", "됐어")]}, tmp_path)
        out = tmp_path / "sig.json"
        extract_signature(scan, out)
        data = json.loads(out.read_text())
        assert data["counters"]["decisive_close"] >= 2

    def test_push_instruction_not_counted(self, tmp_path):
        """'push this branch' should NOT count as decisive_close."""
        scan = _make_scan({"s1": [("user", "push this branch")]}, tmp_path)
        out = tmp_path / "sig.json"
        extract_signature(scan, out)
        data = json.loads(out.read_text())
        assert data["counters"]["decisive_close"] == 0

    def test_merge_instruction_not_counted(self, tmp_path):
        """'merge into main' should NOT count as decisive_close."""
        scan = _make_scan({"s1": [("user", "merge into main")]}, tmp_path)
        out = tmp_path / "sig.json"
        extract_signature(scan, out)
        data = json.loads(out.read_text())
        assert data["counters"]["decisive_close"] == 0

    def test_long_message_not_counted(self, tmp_path):
        """ok buried in a 6-word message should not count."""
        scan = _make_scan({"s1": [("user", "ok that looks good to me now")]}, tmp_path)
        out = tmp_path / "sig.json"
        extract_signature(scan, out)
        data = json.loads(out.read_text())
        assert data["counters"]["decisive_close"] == 0

    def test_assistant_message_ignored(self, tmp_path):
        scan = _make_scan({"s1": [("assistant", "ok done")]}, tmp_path)
        out = tmp_path / "sig.json"
        extract_signature(scan, out)
        data = json.loads(out.read_text())
        assert data["counters"]["decisive_close"] == 0


class TestTargetedRequest:
    def test_file_with_extension_counts(self, tmp_path):
        scan = _make_scan({"s1": [("user", "fix the bug in scripts/honne_py/extract.py")]}, tmp_path)
        out = tmp_path / "sig.json"
        extract_signature(scan, out)
        data = json.loads(out.read_text())
        assert data["counters"]["targeted_request"] >= 1

    def test_file_colon_line_counts(self, tmp_path):
        scan = _make_scan({"s1": [("user", "extract.py:346 에서 수정")]}, tmp_path)
        out = tmp_path / "sig.json"
        extract_signature(scan, out)
        data = json.loads(out.read_text())
        assert data["counters"]["targeted_request"] >= 1

    def test_no_file_reference_not_counted(self, tmp_path):
        scan = _make_scan({"s1": [("user", "이 코드를 수정해주세요")]}, tmp_path)
        out = tmp_path / "sig.json"
        extract_signature(scan, out)
        data = json.loads(out.read_text())
        assert data["counters"]["targeted_request"] == 0


class TestOutputSchema:
    def test_result_schema(self, tmp_path):
        scan = _make_scan({"s1": [("user", "ok"), ("user", "fix.py")]}, tmp_path)
        out = tmp_path / "sig.json"
        assert extract_signature(scan, out) == 0
        data = json.loads(out.read_text())
        assert data["axis"] == "signature"
        assert "counters" in data
        assert "decisive_close" in data["counters"]
        assert "targeted_request" in data["counters"]
        assert "session_coverage" in data
        assert "generated_at" in data

    def test_empty_sessions_returns_2(self, tmp_path):
        p = tmp_path / "empty.json"
        p.write_text(json.dumps({"sessions": []}))
        out = tmp_path / "sig.json"
        assert extract_signature(p, out) == 2
