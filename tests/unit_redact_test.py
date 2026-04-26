"""Unit tests for scripts/_redact.py — 18 sensitive pattern masks.

Each pattern gets an explicit positive case (input → masked marker present,
raw secret absent) plus a shared negative sanity check (ordinary text is
untouched).
"""
import importlib

import pytest

_redact = importlib.import_module("_redact")


@pytest.mark.parametrize(
    "raw,marker,secret",
    [
        ("openai sk-proj-abcdefghijklmnopqrstuvwx12345", "[REDACTED:api-key]", "sk-proj-abcdefghijklmnopqrstuvwx12345"),
        ("stripe pk_live_AAAAAAAAAAAAAAAAAAAAAAA", "[REDACTED:api-key]", "pk_live_AAAAAAAAAAAAAAAAAAAAAAA"),
        ("aws AKIAIOSFODNN7EXAMPLE", "[REDACTED:aws]", "AKIAIOSFODNN7EXAMPLE"),
        ("github ghp_abcdefghijklmnopqrstuvwxyz0123456789ABCD", "[REDACTED:gh]", "ghp_abcdefghijklmnopqrstuvwxyz0123456789ABCD"),
        ("github github_pat_11ABCDEFGH0123456789_abcdefghijklmnopqrstuv", "[REDACTED:gh-pat]", "github_pat_11ABCDEFGH0123456789_abcdefghijklmnopqrstuv"),
        ("slack " + "xox" + "b-0000000000000-0000000000000-AAAAAAAAAAAAAAAA", "[REDACTED:slack-token]", "xox" + "b-0000000000000-0000000000000-AAAAAAAAAAAAAAAA"),
        ("gcp AIzaSyA1234567890abcdefghijklmnopqrstuv", "[REDACTED:gcp-api-key]", "AIzaSyA1234567890abcdefghijklmnopqrstuv"),
        ("-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA\n-----END RSA PRIVATE KEY-----", "[REDACTED:private-key]", "MIIEowIBAAKCAQEA"),
        (
            "jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            "[REDACTED:jwt]",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
        ),
        (
            "slack https://hooks.slack.com/services/TFAKE/BFAKE/FAKE",
            "[REDACTED:slack-webhook]",
            "https://hooks.slack.com/services/TFAKE/BFAKE/FAKE",
        ),
        (
            "discord https://discord.com/api/webhooks/000000000000000000/FAKE_TEST-VALUE",
            "[REDACTED:discord-webhook]",
            "https://discord.com/api/webhooks/000000000000000000/FAKE_TEST-VALUE",
        ),
        ("auth Bearer abc123.def456-ghi789=", "[REDACTED:bearer]", "abc123.def456-ghi789="),
        ("home /Users/jongyun/code/file.ts", "/Users/[REDACTED]/", "/Users/jongyun/"),
        ("home /home/alice/workspace/code.py", "/home/[REDACTED]/", "/home/alice/"),
        ("contact user@example.com", "[REDACTED:email]", "user@example.com"),
        ("phone 010-1234-5678", "[REDACTED:phone]", "010-1234-5678"),
        ("net 192.168.1.100", "[REDACTED:ipv4]", "192.168.1.100"),
        ("card 4532-0151-1283-0366", "[REDACTED:card]", "4532-0151-1283-0366"),
    ],
)
def test_each_pattern_masks(raw, marker, secret):
    out = _redact.redact(raw)
    assert marker in out, f"expected marker {marker!r} in redacted output, got: {out!r}"
    assert secret not in out, f"raw secret {secret!r} still present in output: {out!r}"


def test_query_string_key_redacted_but_prefix_kept():
    out = _redact.redact("url https://api.example.com/?token=supersecret&foo=bar")
    assert "token=[REDACTED]" in out
    assert "supersecret" not in out
    assert "foo=bar" in out  # ordinary query params survive


def test_ordinary_text_untouched():
    raw = "Version v1.2.3 year 2026 chapter 3 — nothing sensitive here."
    assert _redact.redact(raw) == raw


def test_multiple_patterns_same_input():
    raw = "email user@example.com and key sk-proj-abcdefghijklmnopqrstuvwx99999"
    out = _redact.redact(raw)
    assert "[REDACTED:email]" in out
    assert "[REDACTED:api-key]" in out
    assert "user@example.com" not in out
    assert "sk-proj-abcdefghijklmnopqrstuvwx99999" not in out


def test_fixture_file_all_markers_present(tmp_path):
    """Sanity: secrets.txt fixture produces every marker we declare."""
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "secrets.txt"
    out = _redact.redact(fixture.read_text())
    expected_markers = [
        "[REDACTED:api-key]",
        "[REDACTED:aws]",
        "[REDACTED:gh]",
        "[REDACTED:gh-pat]",
        "[REDACTED:gcp-api-key]",
        "[REDACTED:jwt]",
        "[REDACTED:private-key]",
        "[REDACTED:slack-webhook]",
        "[REDACTED:discord-webhook]",
        "[REDACTED:bearer]",
        "/Users/[REDACTED]/",
        "/home/[REDACTED]/",
        "[REDACTED:email]",
        "[REDACTED:phone]",
        "[REDACTED:ipv4]",
        "[REDACTED:card]",
    ]
    missing = [m for m in expected_markers if m not in out]
    assert not missing, f"fixture missed markers: {missing}"


@pytest.mark.parametrize("raw,marker,leak", [
    ("<task-notification>\n<task-id>abc</task-id>\n<output-file>/foo</output-file>\n</task-notification>",
     "[REDACTED:cc-task]", "abc"),
    ("<tool-use-id>toolu_018sT1m1GL1SMGv8MXprFm3W</tool-use-id>",
     "[REDACTED:cc-meta]", "toolu_018sT1m1GL1SMGv8MXprFm3W"),
    ("see toolu_01ABCDEFGHIJKLMNOPQRST in payload",
     "[REDACTED:tool-use-id]", "toolu_01ABCDEFGHIJKLMNOPQRST"),
    ("output at /private/tmp/claude-501/foo/bar",
     "[REDACTED:cc-tmp]", "claude-501/foo"),
])
def test_cc_system_payload_redacted(raw, marker, leak):
    out = _redact.redact(raw)
    assert marker in out
    assert leak not in out


def test_extract_tokenize_filters_stopwords_and_short():
    """extract.py _tokenize: filters stopwords, length<3, and digits."""
    import sys as _sys
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).parent.parent / "scripts"))
    from honne_py.extract import _tokenize
    text = "the docs are in md and json files; render context properly 123"
    toks = list(_tokenize(text))
    # Stopwords/extensions/short dropped
    for stop in ["the", "are", "in", "and", "md", "docs", "json"]:
        assert stop not in toks, f"{stop} should be filtered"
    # Real content survives
    assert "render" in toks
    assert "context" in toks
    assert "properly" in toks
    # Digits are excluded
    assert "123" not in toks


def test_scan_started_at_uses_timestamp_field(tmp_path):
    """scan.py: session.started_at must be filled from JSONL 'timestamp' (not 'ts')."""
    import sys as _sys, json as _json
    from pathlib import Path as _P
    _sys.path.insert(0, str(_P(__file__).parent.parent / "scripts"))
    from honne_py.scan import _parse_jsonl
    fixture = tmp_path / "session.jsonl"
    line = {
        "type": "user", "operation": "msg",
        "timestamp": "2026-04-23T01:00:00Z",
        "sessionId": "sess-test-1234",
        "cwd": "/tmp/proj",
        "message": {"role": "user", "content": "hello world"},
    }
    fixture.write_text(_json.dumps(line) + "\n", encoding="utf-8")
    sess = _parse_jsonl(fixture, redact_secrets=False)
    assert sess is not None
    assert sess["started_at"] == "2026-04-23T01:00:00Z", \
        f"started_at empty (regression): got {sess['started_at']!r}"
