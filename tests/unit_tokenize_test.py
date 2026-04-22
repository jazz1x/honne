"""Unit tests for scripts/_tokenize.py — Unicode word tokenization.

_tokenize.py prints one lowercased token per line for every \\w (minus
underscore) match in stdin. Verified by invoking it as a subprocess with
controlled stdin, since the module itself is top-level script code (not a
callable function).
"""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "_tokenize.py"


def _tokens(text: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=text,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def test_latin_lowercased():
    assert _tokens("Hello World") == ["hello", "world"]


def test_hangul_preserved():
    assert _tokens("일단 해볼게") == ["일단", "해볼게"]


def test_kana_kanji_preserved():
    assert _tokens("コードをチェック") == ["コードをチェック"]


def test_digits_are_tokens():
    assert _tokens("chapter 3 page 42") == ["chapter", "3", "page", "42"]


def test_underscore_splits_tokens():
    """Underscore is NOT in [^\\W_] so it acts as a separator."""
    assert _tokens("foo_bar baz") == ["foo", "bar", "baz"]


def test_mixed_script_line():
    out = _tokens("일단 Let's try 해볼게")
    assert "일단" in out
    assert "let" in out
    assert "s" in out
    assert "try" in out
    assert "해볼게" in out


def test_fixture_file_produces_expected_tokens():
    fixture = Path(__file__).parent / "fixtures" / "lexicon-mixed.txt"
    out = _tokens(fixture.read_text())
    # Presence checks (not strict ordering — file has many lines).
    for expected in ["일단", "해볼게요", "implementation", "コードをチェックします", "123", "456"]:
        assert expected in out, f"expected token {expected!r} missing from {out!r}"
