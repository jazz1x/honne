"""Behavioral tests for detect_recurrence, evidence, purge, io modules."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.detect_recurrence import detect
from honne_py.evidence import gather
from honne_py.purge import purge
from honne_py.io import atomic_write, sha256_file


def _scan_json(path: Path, sessions: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"sessions": sessions}))


class TestDetectRecurrence:
    def test_concept_above_threshold_included(self, tmp_path):
        sessions = [
            {"session_id": f"s{i}", "messages": [{"text": "foo bar baz"}]}
            for i in range(3)
        ]
        inp = tmp_path / "scan.json"
        out = tmp_path / "recurrence.json"
        _scan_json(inp, sessions)

        rc = detect(inp, out, min_sessions=3)
        assert rc == 0
        data = json.loads(out.read_text())
        concepts = [d["concept"] for d in data]
        assert "foo bar baz" in concepts

    def test_concept_below_threshold_excluded(self, tmp_path):
        sessions = [
            {"session_id": "s1", "messages": [{"text": "foo bar baz"}]},
            {"session_id": "s2", "messages": [{"text": "foo bar baz"}]},
        ]
        inp = tmp_path / "scan.json"
        out = tmp_path / "recurrence.json"
        _scan_json(inp, sessions)

        rc = detect(inp, out, min_sessions=3)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data == []

    def test_empty_sessions_returns_2(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "recurrence.json"
        _scan_json(inp, [])
        assert detect(inp, out) == 2

    def test_missing_input_returns_1(self, tmp_path):
        assert detect(tmp_path / "missing.json", tmp_path / "out.json") == 1

    def test_sorted_by_count_desc(self, tmp_path):
        sessions = [
            {"session_id": f"s{i}", "messages": [{"text": "rare one time and common recurring pattern"}]}
            for i in range(5)
        ]
        inp = tmp_path / "scan.json"
        out = tmp_path / "recurrence.json"
        _scan_json(inp, sessions)

        rc = detect(inp, out, min_sessions=3)
        assert rc == 0
        data = json.loads(out.read_text())
        counts = [d["count"] for d in data]
        assert counts == sorted(counts, reverse=True)


class TestEvidenceGather:
    def _make_scan(self, path, sessions):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"sessions": sessions}))

    def test_claim_matched_returns_0(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "evidence.json"
        sessions = [{"session_id": "s1", "messages": [{"text": "the solution is obvious"}]}]
        self._make_scan(inp, sessions)

        rc = gather(inp, "solution", out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert len(data) == 1
        assert data[0]["session_id"] == "s1"

    def test_claim_not_found_returns_2(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "evidence.json"
        sessions = [{"session_id": "s1", "messages": [{"text": "nothing relevant here"}]}]
        self._make_scan(inp, sessions)

        rc = gather(inp, "xyzzy", out)
        assert rc == 2

    def test_max_respected(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "evidence.json"
        sessions = [
            {"session_id": f"s{i}", "messages": [{"text": "target word in message"}]}
            for i in range(10)
        ]
        self._make_scan(inp, sessions)

        rc = gather(inp, "target", out, max_=3)
        assert rc == 0
        data = json.loads(out.read_text())
        assert len(data) <= 3

    def test_missing_input_returns_1(self, tmp_path):
        assert gather(tmp_path / "missing.json", "x", tmp_path / "out.json") == 1

    def test_case_insensitive_match(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "evidence.json"
        sessions = [{"session_id": "s1", "messages": [{"text": "The SOLUTION is obvious"}]}]
        self._make_scan(inp, sessions)

        rc = gather(inp, "Solution", out)
        assert rc == 0


class TestPurge:
    def test_no_flag_returns_1(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert purge(all_=False, keep_assets=False, force=True) == 1

    def test_no_honne_dir_returns_0(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        assert purge(all_=True, force=True) == 0

    def test_all_force_deletes_honne(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        honne = tmp_path / ".honne"
        (honne / "cache").mkdir(parents=True)
        (honne / "assets").mkdir()

        rc = purge(all_=True, force=True)
        assert rc == 0
        assert not honne.exists()

    def test_keep_assets_force_keeps_assets_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        honne = tmp_path / ".honne"
        (honne / "cache").mkdir(parents=True)
        (honne / "assets" / "claims.jsonl").parent.mkdir(parents=True)
        (honne / "assets" / "claims.jsonl").write_text("")
        (honne / "cache" / "scan.json").write_text("{}")

        rc = purge(keep_assets=True, force=True)
        assert rc == 0
        assert (honne / "assets").exists()
        assert not (honne / "cache").exists()

    def test_symlink_refused(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        target = tmp_path / "real_honne"
        target.mkdir()
        (tmp_path / ".honne").symlink_to(target)

        rc = purge(all_=True, force=True)
        assert rc == 1


class TestIO:
    def test_atomic_write_creates_file(self, tmp_path):
        out = tmp_path / "sub" / "file.json"
        atomic_write(out, '{"key": "val"}')
        assert out.exists()
        assert out.read_text() == '{"key": "val"}'

    def test_atomic_write_bytes(self, tmp_path):
        out = tmp_path / "file.bin"
        atomic_write(out, b"binary data")
        assert out.read_bytes() == b"binary data"

    def test_atomic_write_overwrites(self, tmp_path):
        out = tmp_path / "file.txt"
        atomic_write(out, "first")
        atomic_write(out, "second")
        assert out.read_text() == "second"

    def test_sha256_file_correct(self, tmp_path):
        import hashlib
        f = tmp_path / "data.txt"
        f.write_bytes(b"hello world")
        expected = hashlib.sha256(b"hello world").hexdigest()
        assert sha256_file(f) == expected

    def test_sha256_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_bytes(b"content a")
        f2.write_bytes(b"content b")
        assert sha256_file(f1) != sha256_file(f2)
