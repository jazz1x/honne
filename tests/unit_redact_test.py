"""Unit tests for scripts/_redact.py — 12 sensitive pattern masks.

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
        "[REDACTED:jwt]",
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
