"""Boundary tests for reaction, workflow, ritual, obsession, antipattern extractors."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.extract import (
    extract_reaction,
    extract_workflow,
    extract_ritual,
    extract_obsession,
    extract_antipattern,
)


def _write_scan(path: Path, sessions: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"sessions": sessions}))


def _session(sid: str, messages: list, started_at: str = "2025-01-01T00:00:00Z") -> dict:
    return {"session_id": sid, "started_at": started_at, "messages": messages}


def _user(text: str) -> dict:
    return {"role": "user", "text": text}


def _assistant(text: str) -> dict:
    return {"role": "assistant", "text": text}


# ── Reaction ──────────────────────────────────────────────────────────────────

class TestExtractReaction:
    def test_missing_file_returns_1(self, tmp_path):
        assert extract_reaction(tmp_path / "missing.json", tmp_path / "out.json") == 1

    def test_empty_sessions_returns_2(self, tmp_path):
        inp = tmp_path / "scan.json"
        _write_scan(inp, [])
        assert extract_reaction(inp, tmp_path / "out.json") == 2

    def test_correction_pattern_detected(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("that is wrong"), _assistant("ok")])])

        rc = extract_reaction(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["correction"] >= 1

    def test_approval_pattern_detected(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("perfect!")])])

        rc = extract_reaction(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["approval"] >= 1

    def test_no_reaction_pattern_counters_all_zero(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("implement the feature")])])

        rc = extract_reaction(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert all(v == 0 for v in data["counters"].values())

    def test_session_coverage_tracked(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        sessions = [
            _session("s1", [_user("wrong answer")]),
            _session("s2", [_user("looks good")]),
            _session("s3", [_user("no reaction keywords here really")]),
        ]
        _write_scan(inp, sessions)

        rc = extract_reaction(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["session_coverage"]["total_sessions"] == 3
        assert data["session_coverage"]["matched_sessions"] >= 1

    def test_output_axis_field(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("good")])])
        extract_reaction(inp, out)
        data = json.loads(out.read_text())
        assert data["axis"] == "reaction"


# ── Workflow ──────────────────────────────────────────────────────────────────

class TestExtractWorkflow:
    def test_missing_file_returns_1(self, tmp_path):
        assert extract_workflow(tmp_path / "missing.json", tmp_path / "out.json") == 1

    def test_empty_sessions_returns_2(self, tmp_path):
        inp = tmp_path / "scan.json"
        _write_scan(inp, [])
        assert extract_workflow(inp, tmp_path / "out.json") == 2

    def test_question_driven_from_question_mark(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("how does this work?")])])

        rc = extract_workflow(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["question_driven"] >= 1

    def test_code_first_from_backtick(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("```python\nprint('hi')\n```")])])

        rc = extract_workflow(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["code_first"] >= 1

    def test_multi_file_scope_from_two_paths(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("look at src/foo.py and tests/bar.py")])])

        rc = extract_workflow(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["multi_file_scope"] >= 1

    def test_top_examples_populated(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("why does this fail?")])])

        extract_workflow(inp, out)
        data = json.loads(out.read_text())
        assert len(data["top_examples"]) >= 1
        assert "key" in data["top_examples"][0]

    def test_output_axis_field(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("task")])])
        extract_workflow(inp, out)
        assert json.loads(out.read_text())["axis"] == "workflow"


# ── Ritual ────────────────────────────────────────────────────────────────────

class TestExtractRitual:
    def test_missing_file_returns_1(self, tmp_path):
        assert extract_ritual(tmp_path / "missing.json", tmp_path / "out.json") == 1

    def test_empty_sessions_returns_2(self, tmp_path):
        inp = tmp_path / "scan.json"
        _write_scan(inp, [])
        assert extract_ritual(inp, tmp_path / "out.json") == 2

    def test_direct_command_classified(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("run the tests now")])])

        rc = extract_ritual(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["direct_command"] >= 1

    def test_question_classified(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("what is this?")])])

        rc = extract_ritual(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["question"] >= 1

    def test_task_description_is_default(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("implement a new feature for user login")])])

        rc = extract_ritual(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["task_description"] >= 1

    def test_only_first_message_counted_per_session(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [
            _user("implement login"),
            _user("run the tests now"),  # second message should NOT change ritual
        ])])

        rc = extract_ritual(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["task_description"] == 1
        assert data["counters"]["direct_command"] == 0

    def test_output_axis_field(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("task")])])
        extract_ritual(inp, out)
        assert json.loads(out.read_text())["axis"] == "ritual"


# ── Obsession ─────────────────────────────────────────────────────────────────

class TestExtractObsession:
    def test_missing_file_returns_1(self, tmp_path):
        assert extract_obsession(tmp_path / "missing.json", tmp_path / "out.json") == 1

    def test_empty_sessions_returns_2(self, tmp_path):
        inp = tmp_path / "scan.json"
        _write_scan(inp, [])
        assert extract_obsession(inp, tmp_path / "out.json") == 2

    def test_repeated_preamble_counted(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        sessions = [
            _session(f"s{i}", [_user("why does this keep failing every time")])
            for i in range(3)
        ]
        _write_scan(inp, sessions)

        rc = extract_obsession(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert len(data["top_preambles"]) >= 1
        assert data["top_preambles"][0]["count"] == 3

    def test_ko_language_split(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        sessions = [
            _session("s1", [_user("안녕하세요 이것은 한국어 테스트입니다 잘 되고 있나요")])
        ]
        _write_scan(inp, sessions)

        rc = extract_obsession(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["language_split"]["ko"] >= 1

    def test_en_language_split(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        sessions = [
            _session("s1", [_user("this is a purely english language message about testing")])
        ]
        _write_scan(inp, sessions)

        rc = extract_obsession(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["language_split"]["en"] >= 1

    def test_top_preambles_capped_at_5(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        sessions = [
            _session(f"s{i}", [_user(f"unique preamble number {i} for this test session")])
            for i in range(10)
        ]
        _write_scan(inp, sessions)

        rc = extract_obsession(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert len(data["top_preambles"]) <= 5

    def test_output_axis_field(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("hello")])])
        extract_obsession(inp, out)
        assert json.loads(out.read_text())["axis"] == "obsession"


# ── Antipattern ───────────────────────────────────────────────────────────────

class TestExtractAntipattern:
    def test_missing_file_returns_1(self, tmp_path):
        assert extract_antipattern(tmp_path / "missing.json", tmp_path / "out.json") == 1

    def test_empty_sessions_returns_2(self, tmp_path):
        inp = tmp_path / "scan.json"
        _write_scan(inp, [])
        assert extract_antipattern(inp, tmp_path / "out.json") == 2

    def test_overspec_detected(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("you must ALWAYS do this exactly")])])

        rc = extract_antipattern(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["overspec"] >= 1

    def test_repeat_same_request_detected(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [
            _user("fix the bug"),
            _user("fix the bug"),
        ])])

        rc = extract_antipattern(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["repeat_same_request"] >= 1

    def test_no_antipattern_counters_zero(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("implement a clean feature")])])

        rc = extract_antipattern(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["overspec"] == 0
        assert data["counters"]["repeat_same_request"] == 0

    def test_repeat_whitespace_normalized(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [
            _user("fix  the  bug"),
            _user("fix the bug"),
        ])])

        rc = extract_antipattern(inp, out)
        assert rc == 0
        data = json.loads(out.read_text())
        assert data["counters"]["repeat_same_request"] >= 1

    def test_output_axis_field(self, tmp_path):
        inp = tmp_path / "scan.json"
        out = tmp_path / "out.json"
        _write_scan(inp, [_session("s1", [_user("implement")])])
        extract_antipattern(inp, out)
        assert json.loads(out.read_text())["axis"] == "antipattern"
