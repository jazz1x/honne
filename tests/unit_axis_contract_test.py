"""T11: axis.py contract tests — collect_quotes, run(), validate(), AXES coverage."""
import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from honne_py.axis import AXES, collect_quotes, run, validate

SEED_SCAN = Path(__file__).parent / "fixtures" / "seed_scan.json"
EMPTY_SCAN = Path(__file__).parent / "fixtures" / "empty_scan.json"

pytestmark = pytest.mark.skipif(
    not SEED_SCAN.exists(),
    reason="seed_scan.json absent — regenerate locally via `honne scan` before running contract tests",
)


# ── AXES constant ──────────────────────────────────────────────────────────────

def test_axes_count():
    assert len(AXES) == 7


def test_axes_values():
    expected = {"lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern", "signature"}
    assert set(AXES) == expected


# ── run() exit codes ───────────────────────────────────────────────────────────

def test_run_unknown_axis_returns_2(tmp_path):
    dummy = tmp_path / "scan.json"
    dummy.write_text('{"sessions":[]}')
    assert run("nonexistent", "ko", dummy) == 2


def test_run_unknown_locale_returns_2():
    assert run("lexicon", "xx", SEED_SCAN) == 2


def test_run_missing_scan_returns_66(tmp_path):
    assert run("lexicon", "ko", tmp_path / "no_such.json") == 66


def test_run_empty_scan_returns_0_insufficient(capsys):
    rc = run("lexicon", "ko", EMPTY_SCAN)
    assert rc == 0
    out = capsys.readouterr().out
    d = json.loads(out)
    assert d["insufficient_evidence"] is True
    assert d["quotes"] == []


def test_run_seed_returns_0(capsys):
    rc = run("lexicon", "ko", SEED_SCAN)
    assert rc == 0
    out = capsys.readouterr().out
    d = json.loads(out)
    assert d["axis"] == "lexicon"


# ── test_each_axis_yields_quotes_on_seed (finding 10) ─────────────────────────

@pytest.mark.parametrize("axis", AXES)
def test_each_axis_yields_quotes_on_seed(axis, capsys):
    """Every axis must produce ≥ 1 quote from the seed scan (T9.5 invariant)."""
    rc = run(axis, "ko", SEED_SCAN)
    assert rc == 0
    out = capsys.readouterr().out
    d = json.loads(out)
    assert d["insufficient_evidence"] is False, f"{axis}: insufficient_evidence=True"
    assert len(d["quotes"]) >= 1, f"{axis}: 0 quotes"


# ── collect_quotes schema ──────────────────────────────────────────────────────

def test_collect_quotes_schema():
    import honne_py.io as honne_io
    from honne_py.extract import extract_lexicon
    import tempfile, os
    tmp = Path(tempfile.mktemp(suffix=".json"))
    extract_lexicon(input_path=SEED_SCAN, out_path=tmp)
    signal = honne_io.load_cache(tmp)
    tmp.unlink(missing_ok=True)

    quotes = collect_quotes(SEED_SCAN, "lexicon", signal, k=3)
    for q in quotes:
        assert "session_id" in q
        assert "text" in q
        assert "ts" in q
        assert "frequency" in q
        assert "key" in q
        assert len(q["text"]) <= 201  # 200 chars + ellipsis


def test_collect_quotes_no_duplicate_texts():
    """Duplicate texts must not appear across keys."""
    import honne_py.io as honne_io
    from honne_py.extract import extract_reaction
    import tempfile
    tmp = Path(tempfile.mktemp(suffix=".json"))
    extract_reaction(input_path=SEED_SCAN, out_path=tmp)
    signal = honne_io.load_cache(tmp)
    tmp.unlink(missing_ok=True)
    quotes = collect_quotes(SEED_SCAN, "reaction", signal, k=3)
    texts = [q["text"] for q in quotes]
    assert len(texts) == len(set(texts)), "duplicate texts in collect_quotes output"


# ── validate() exit codes ──────────────────────────────────────────────────────

def test_validate_pass():
    assert validate("이 표현은 매우 특이하고 구체적이다", "ko") == 0


def test_validate_short_text_returns_2():
    assert validate("짧음", "ko") == 2


def test_validate_forbidden_phrase_ko():
    assert validate("때로는 그럴 수 있어", "ko") == 2  # "때로는" in forbidden


def test_validate_forbidden_phrase_en():
    assert validate("sometimes it depends", "en") == 2  # "sometimes"


def test_validate_unknown_locale_returns_2():
    assert validate("any text here for test", "xx") == 2


def test_validate_skip_if_overlaps_returns_3():
    text = "이 표현은 매우 특이하고 구체적이다"
    assert validate(text, "ko", skip_if_overlaps=text) == 3


def test_validate_skip_if_overlaps_no_match():
    assert validate("이 표현은 매우 특이하고 구체적이다", "ko", skip_if_overlaps="전혀 다른 텍스트") == 0


# ── E4: text < 8 chars ─────────────────────────────────────────────────────────

def test_validate_exactly_8_chars_passes():
    assert validate("12345678", "en") == 0


def test_validate_7_chars_fails():
    assert validate("1234567", "en") == 2
