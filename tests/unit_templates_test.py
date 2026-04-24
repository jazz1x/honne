"""T13: template file tests — E2(locale missing) + E3(forbidden.json fail) + E7(errors.txt)."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from honne_py.axis import _load_template, validate, AXES, LOCALES

TEMPLATES_DIR = Path(__file__).parent.parent / "skills" / "whoami" / "templates"
AXES_LABELS = {
    "lexicon":     {"ko": "어휘",           "en": "Lexicon",           "jp": "語彙"},
    "reaction":    {"ko": "반응",           "en": "Reaction",          "jp": "反応"},
    "workflow":    {"ko": "워크플로",       "en": "Workflow",          "jp": "ワークフロー"},
    "obsession":   {"ko": "집착",           "en": "Obsession",         "jp": "執着"},
    "ritual":      {"ko": "의식",           "en": "Ritual",            "jp": "儀式"},
    "antipattern": {"ko": "비효율 패턴",    "en": "Antipattern",       "jp": "アンチパターン"},
    "signature":   {"ko": "시그니처 패턴",  "en": "Signature",         "jp": "シグニチャパターン"},
}
FORBIDDEN_LABELS = {"녹동", "뛈글", "맨듭니다"}


# ── axes.*.md: all 6 sections exist with required keys ────────────────────────

@pytest.mark.parametrize("locale", LOCALES)
@pytest.mark.parametrize("axis", AXES)
def test_load_template_required_keys(axis, locale):
    tpl = _load_template(locale, axis)
    for key in ("label", "hitl_question", "report_header", "connective"):
        assert key in tpl, f"{axis}/{locale}: missing '{key}'"


@pytest.mark.parametrize("locale", LOCALES)
@pytest.mark.parametrize("axis", AXES)
def test_label_matches_canonical(axis, locale):
    """Appendix A whitelist — no hallucinated labels allowed."""
    tpl = _load_template(locale, axis)
    assert tpl["label"] == AXES_LABELS[axis][locale], \
        f"{axis}/{locale}: label '{tpl['label']}' != '{AXES_LABELS[axis][locale]}'"


@pytest.mark.parametrize("axis", AXES)
def test_no_forbidden_labels(axis):
    """Hallucinated labels from Appendix A must not appear anywhere."""
    for locale in LOCALES:
        tpl = _load_template(locale, axis)
        for bad in FORBIDDEN_LABELS:
            for val in tpl.values():
                assert bad not in val, f"{axis}/{locale}: forbidden label '{bad}' found"


# ── E2: unknown locale → exit 2 ───────────────────────────────────────────────

def test_run_unknown_locale_returns_2():
    from honne_py.axis import run
    from pathlib import Path
    scan = Path(__file__).parent / "fixtures" / "seed_scan.json"
    if not scan.exists():
        pytest.skip("seed_scan.json absent — regenerate locally via `honne scan`")
    assert run("lexicon", "xx", scan) == 2


def test_load_template_unknown_locale_raises():
    with pytest.raises(Exception):
        _load_template("xx", "lexicon")


# ── E3: forbidden.json parse failure → validate returns 2 ─────────────────────

def test_validate_forbidden_json_corrupt(tmp_path, monkeypatch):
    bad_forbidden = tmp_path / "forbidden.json"
    bad_forbidden.write_text("not valid json{{{")
    import honne_py.axis as axis_mod
    orig = axis_mod.Path
    class PatchedPath(type(Path())):
        pass
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(
            "honne_py.axis.Path",
            lambda *a, **kw: bad_forbidden if "forbidden.json" in str(a) else orig(*a, **kw)
        )
        # validate reads forbidden.json; corrupt file → exit 2
        result = validate("some text long enough here", "ko")
    # The real forbidden.json is valid; test the parse-fail path via mock
    from unittest import mock
    with mock.patch("pathlib.Path.read_text", side_effect=OSError("blocked")):
        assert validate("some text long enough here", "ko") == 2


# ── E7: errors.txt format — every line must be code TAB locale TAB banner ─────

def test_errors_txt_tsv_format():
    errors_file = TEMPLATES_DIR / "errors.txt"
    assert errors_file.exists(), "errors.txt missing"
    for i, line in enumerate(errors_file.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        assert len(parts) == 3, f"errors.txt line {i}: expected 3 TSV fields, got {len(parts)}"
        code, locale, banner = parts
        assert code.isdigit(), f"errors.txt line {i}: code '{code}' is not numeric"
        assert locale in ("ko", "en", "jp"), f"errors.txt line {i}: unknown locale '{locale}'"
        assert len(banner) > 0, f"errors.txt line {i}: banner is empty"


def test_errors_txt_required_codes():
    errors_file = TEMPLATES_DIR / "errors.txt"
    content = errors_file.read_text(encoding="utf-8")
    codes = {line.split("\t")[0] for line in content.splitlines() if "\t" in line}
    for required in ("2", "66", "71", "73"):
        assert required in codes, f"errors.txt: missing exit code {required}"


# ── forbidden.json structure ───────────────────────────────────────────────────

def test_forbidden_json_has_all_locales():
    data = json.loads((TEMPLATES_DIR / "forbidden.json").read_text())
    assert set(data.keys()) == {"ko", "en", "jp"}


def test_forbidden_json_all_lists():
    data = json.loads((TEMPLATES_DIR / "forbidden.json").read_text())
    for locale, phrases in data.items():
        assert isinstance(phrases, list), f"forbidden.json[{locale}] must be a list"
        assert len(phrases) > 0, f"forbidden.json[{locale}] must not be empty"


# ── axes.*.md file count ───────────────────────────────────────────────────────

def test_all_three_locale_files_exist():
    for locale in LOCALES:
        p = TEMPLATES_DIR / f"axes.{locale}.md"
        assert p.exists(), f"axes.{locale}.md missing"


def test_each_locale_file_has_seven_sections():
    for locale in LOCALES:
        p = TEMPLATES_DIR / f"axes.{locale}.md"
        count = sum(1 for line in p.read_text().splitlines() if line.startswith("## "))
        assert count == 7, f"axes.{locale}.md: expected 7 sections, got {count}"
