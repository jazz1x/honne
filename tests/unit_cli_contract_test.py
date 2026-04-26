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


def test_record_claim_malformed_quotes_json(tmp_path):
    out = tmp_path / "claims.jsonl"
    rc = main(["record", "claim",
               "--type", "claim", "--axis", "lexicon",
               "--scope", "repo", "--claim", "test",
               "--out", str(out),
               "--quotes-json", '{bad json}'])
    assert rc == 1


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


# ── render persona narrative inject (CLI integration) ────────────────────────

def test_cli_render_persona_passes_narrative(tmp_path):
    """CLI must forward --narrative to render_persona; regression for v2 silent drop."""
    import json
    claims = tmp_path / "claims.jsonl"
    narrative = tmp_path / "narrative.json"
    out = tmp_path / "persona.json"

    claims.write_text(json.dumps({
        "id": "c1", "type": "claim", "axis": "lexicon", "scope": "repo",
        "run_id": "r1", "claim": "test claim",
        "quotes": [{"session_id": "s1", "ts": "2026-01-01T00:00:00Z",
                    "text": "x", "frequency": 1, "key": "x"}],
        "created_at": "2026-01-01T00:00:00Z",
    }) + "\n", encoding="utf-8")
    narrative.write_text(json.dumps({
        "axes": {"lexicon": "expected explanation",
                 "reaction": None, "workflow": None,
                 "obsession": None, "ritual": None, "antipattern": None},
        "oneliner": "expected oneliner",
    }), encoding="utf-8")

    rc = main(["render", "persona",
               "--claims", str(claims), "--scope", "repo", "--locale", "ko",
               "--run-id", "r1", "--now", "2026-01-01T00:00:00Z",
               "--narrative", str(narrative), "--out", str(out)])
    assert rc == 0
    persona = json.loads(out.read_text(encoding="utf-8"))
    assert persona["oneliner"] == "expected oneliner", \
        "CLI dropped --narrative — render_persona received no narrative_path"
    assert persona["axes"]["lexicon"]["explanation"] == "expected explanation"


# ── render personas (0.0.2) ──────────────────────────────────────────────────

def test_render_personas_args(tmp_path):
    synthesis = tmp_path / "synthesis.json"
    persona = tmp_path / "persona.json"
    out_dir = tmp_path / "personas"
    with patch("honne_py.persona_prompt.render_personas", return_value=0):
        main(["render", "personas",
              "--synthesis", str(synthesis),
              "--persona", str(persona),
              "--locale", "ko",
              "--out-dir", str(out_dir)])


# ── persona check (0.0.2) ───────────────────────────────────────────────────

def test_persona_check_exists(tmp_path):
    persona = tmp_path / "persona.json"
    persona.write_text("{}")
    rc = main(["persona", "check", "--persona", str(persona)])
    assert rc == 0


def test_persona_check_missing(tmp_path):
    persona = tmp_path / "nonexistent.json"
    rc = main(["persona", "check", "--persona", str(persona)])
    assert rc == 66


# ── ritual frequency (counters lookup) ───────────────────────────────────────

def test_summarize_ritual_uses_counters_for_frequency():
    """summarize_ritual must read frequency from signal['counters'][key], not from top_examples."""
    from honne_py.summarize import summarize_ritual
    signal = {
        "counters": {"task_description": 390, "question": 9, "direct_command": 3},
        "top_examples": [
            {"key": "task_description", "first_text": "do the thing",
             "first_session_id": "s1", "first_ts": "t1"},
            {"key": "question", "first_text": "what is this?",
             "first_session_id": "s2", "first_ts": "t2"},
        ],
    }
    out = summarize_ritual(signal, "ko")
    assert "(390)" in out, f"frequency 390 missing — counters lookup broken: {out!r}"
    assert "(9)" in out
    assert "(0)" not in out, f"freq=0 leak (regression): {out!r}"
