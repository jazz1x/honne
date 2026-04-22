"""CLI contract tests: every subcommand must accept all args from PRD §3.3."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.cli import main


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_ok(*args):
    """Assert main() parses argv without raising and returns early (args valid)."""
    # We only test arg parsing — stop before actual I/O by patching dispatch.
    with patch("honne_py.cli.run_scan", return_value=0), \
         patch("honne_py.cli.extract_lexicon", return_value=0, create=True), \
         patch("honne_py.cli.detect", return_value=0, create=True), \
         patch("honne_py.cli.gather", return_value=0, create=True), \
         patch("honne_py.cli.index_session", return_value=0, create=True), \
         patch("honne_py.cli.query", return_value=0, create=True), \
         patch("honne_py.cli.record_claim", return_value=0, create=True), \
         patch("honne_py.cli.purge", return_value=0, create=True), \
         patch("honne_py.cli.precommit", return_value=0, create=True):
        try:
            main(list(args))
        except SystemExit as e:
            if e.code not in (0, None, 2):
                pytest.fail(f"Unexpected exit {e.code} for argv={args}")


def _parse_exit1(*args):
    """Assert main() exits with code 1 for bad args."""
    with pytest.raises(SystemExit) as exc_info:
        main(list(args))
    assert exc_info.value.code == 1, f"Expected exit 1, got {exc_info.value.code}"


# ── version guard ─────────────────────────────────────────────────────────────

def test_version_guard_python38(monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 8, 0))
    result = main([])
    assert result == 4


# ── --help / --version ────────────────────────────────────────────────────────

def test_help():
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0


def test_version():
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0


# ── scan ──────────────────────────────────────────────────────────────────────

def test_scan_minimal(tmp_path):
    cache = tmp_path / "scan.json"
    with patch("honne_py.scan.run_scan", return_value=0):
        main(["scan", "--scope", "repo", "--since", "2020-01-01",
              "--cache", str(cache)])


def test_scan_all_args(tmp_path):
    cache = tmp_path / "scan.json"
    idx = tmp_path / "index.json"
    with patch("honne_py.scan.run_scan", return_value=0):
        main(["scan", "--scope", "global", "--since", "2023-01-01",
              "--cache", str(cache), "--index-ref", str(idx)])


def test_scan_no_cache_uses_default(tmp_path, monkeypatch):
    """--cache omitted must not crash; default path is used."""
    monkeypatch.chdir(tmp_path)
    with patch("honne_py.scan.run_scan", return_value=0) as mock_scan:
        main(["scan", "--scope", "repo"])
    called_cache = mock_scan.call_args.kwargs.get("cache") or mock_scan.call_args[1].get("cache") or mock_scan.call_args[0][2]
    assert called_cache is not None
    assert "scan.json" in str(called_cache)


def test_scan_unknown_arg():
    _parse_exit1("scan", "--bogus")


# ── extract lexicon ──────────────────────────────────────────────────────────

def test_extract_lexicon_args(tmp_path):
    inp = tmp_path / "scan.json"
    out = tmp_path / "lex.json"
    with patch("honne_py.extract.extract_lexicon", return_value=0):
        main(["extract", "lexicon",
              "--input", str(inp), "--out", str(out),
              "--top", "30", "--min-sessions", "2"])


# ── detect-recurrence ────────────────────────────────────────────────────────

def test_detect_recurrence_args(tmp_path):
    inp = tmp_path / "scan.json"
    out = tmp_path / "recur.json"
    with patch("honne_py.detect_recurrence.detect", return_value=0):
        main(["detect-recurrence",
              "--input", str(inp), "--out", str(out), "--min-sessions", "5"])


# ── evidence ─────────────────────────────────────────────────────────────────

def test_evidence_gather_args(tmp_path):
    inp = tmp_path / "scan.json"
    out = tmp_path / "ev.json"
    with patch("honne_py.evidence.gather", return_value=0):
        main(["evidence", "gather",
              "--input", str(inp), "--claim", "test claim",
              "--out", str(out), "--max", "5"])


# ── index ─────────────────────────────────────────────────────────────────────

def test_index_session_args(tmp_path):
    jsonl = tmp_path / "session.jsonl"
    out = tmp_path / "idx.json"
    with patch("honne_py.index.index_session", return_value=0):
        main(["index", "session", "--jsonl", str(jsonl), "--out", str(out)])


# ── query ─────────────────────────────────────────────────────────────────────

def test_query_all_args(tmp_path):
    out = tmp_path / "q.json"
    with patch("honne_py.query.query", return_value=0):
        main(["query",
              "--base-dir", str(tmp_path),
              "--scope", "repo",
              "--since", "2023-01-01", "--until", "2026-12-31",
              "--tag", "lexicon", "--tags", "lexicon,reaction",
              "--type", "claim", "--types", "claim,pattern",
              "--out", str(out)])


# ── record ────────────────────────────────────────────────────────────────────

def test_record_claim_args(tmp_path):
    out = tmp_path / "claims.jsonl"
    with patch("honne_py.record.record_claim", return_value=0):
        main(["record", "claim",
              "--type", "claim", "--axis", "lexicon",
              "--scope", "repo", "--claim", "test",
              "--out", str(out),
              "--support-count", "3",
              "--prior-id", "abc123",
              "--quotes-json", '["quote1"]'])


# ── purge ─────────────────────────────────────────────────────────────────────

def test_purge_all_force(tmp_path):
    with patch("honne_py.purge.purge", return_value=0):
        main(["purge", "--all", "--force"])


def test_purge_keep_assets(tmp_path):
    with patch("honne_py.purge.purge", return_value=0):
        main(["purge", "--keep-assets", "--force"])


def test_purge_unknown_arg():
    _parse_exit1("purge", "--bogus")


# ── precommit ─────────────────────────────────────────────────────────────────

def test_precommit(tmp_path):
    with patch("honne_py.precommit.precommit", return_value=0):
        main(["precommit"])
