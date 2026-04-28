"""Unit tests for scan.py since-filter date normalization."""
import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.scan import run_scan


def _write_jsonl(path: Path, messages: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        f.write('{"sessionId":"test-session","cwd":"/test","timestamp":"2025-01-01T00:00:00Z"}\n')
        for m in messages:
            record = {
                "message": {"role": m.get("role", "user"), "content": m.get("text", "")},
                "timestamp": m.get("ts", "2025-01-01T00:00:00Z"),
            }
            f.write(json.dumps(record) + "\n")


class TestSinceFilter:
    def test_since_date_only_includes_files_on_same_date(self, tmp_path, monkeypatch):
        """Files with mtime on `since` date must NOT be excluded (was the bug)."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("PWD", "/test-project")

        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        project_dir.mkdir(parents=True)
        session = project_dir / "session.jsonl"
        _write_jsonl(session, [{"role": "user", "text": "hello", "ts": "2025-06-01T10:00:00Z"}])

        mtime = session.stat().st_mtime
        mtime_date = time.strftime("%Y-%m-%d", time.localtime(mtime))

        cache = tmp_path / ".honne" / "cache" / "scan.json"
        rc = run_scan(scope="repo", since=mtime_date, cache=cache, base_dir=tmp_path / ".honne")
        assert rc == 0
        data = json.loads(cache.read_text())
        assert len(data["sessions"]) >= 1, "File on `since` date must be included"

    def test_since_datetime_string_normalized(self, tmp_path, monkeypatch):
        """since='2025-06-01T00:00:00Z' must not exclude files from 2025-06-01."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("PWD", "/test-project")

        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        project_dir.mkdir(parents=True)
        session = project_dir / "session.jsonl"
        _write_jsonl(session, [{"role": "user", "text": "hello", "ts": "2025-06-01T10:00:00Z"}])

        mtime = session.stat().st_mtime
        mtime_date = time.strftime("%Y-%m-%d", time.localtime(mtime))
        since_full = mtime_date + "T00:00:00Z"

        cache = tmp_path / ".honne" / "cache" / "scan.json"
        rc = run_scan(scope="repo", since=since_full, cache=cache, base_dir=tmp_path / ".honne")
        assert rc == 0
        data = json.loads(cache.read_text())
        assert len(data["sessions"]) >= 1, "File must be included when since has time component"

    def test_since_future_date_excludes_all(self, tmp_path, monkeypatch):
        """since far in future → empty sessions."""
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("PWD", "/test-project")

        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        project_dir.mkdir(parents=True)
        session = project_dir / "session.jsonl"
        _write_jsonl(session, [{"role": "user", "text": "hello", "ts": "2025-01-01T00:00:00Z"}])

        cache = tmp_path / ".honne" / "cache" / "scan.json"
        rc = run_scan(scope="repo", since="2099-01-01", cache=cache, base_dir=tmp_path / ".honne")
        assert rc == 2
