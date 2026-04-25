"""Contract tests for honne:crush skill."""
import re
from pathlib import Path


SKILL_ROOT = Path(__file__).parent.parent / "skills/crush"


def _read_skill(locale: str) -> str:
    suffix = f".{locale}" if locale != "en" else ""
    path = SKILL_ROOT / f"SKILL{suffix}.md"
    return path.read_text(encoding="utf-8")


class TestCrushSkillFilesExist:
    """Test that crush SKILL files exist."""

    def test_all_locales_exist(self):
        for locale in ["en", "ko", "jp"]:
            suffix = f".{locale}" if locale != "en" else ""
            path = SKILL_ROOT / f"SKILL{suffix}.md"
            assert path.exists(), f"SKILL{suffix}.md missing"

    def test_version_matches_across_locales(self):
        versions = {}
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            m = re.search(r"^version: (.+?)$", content, re.MULTILINE)
            assert m, f"version missing in SKILL ({locale})"
            versions[locale] = m.group(1).strip()
        assert len(set(versions.values())) == 1, f"Version mismatch: {versions}"
        assert "0.0.2" in list(versions.values())[0], "Version should be 0.0.2"

    def test_name_is_crush(self):
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            m = re.search(r"^name: (.+?)$", content, re.MULTILINE)
            assert m, f"name missing in SKILL ({locale})"
            assert m.group(1).strip() == "crush", f"name not 'crush' in SKILL ({locale})"


class TestCrushStepStructure:
    """Test that crush SKILL has required 6 steps."""

    def test_steps_present_english(self):
        content = _read_skill("en")
        for step in range(1, 7):
            assert f"## Step {step}:" in content, f"Step {step} missing in English"

    def test_steps_present_korean(self):
        content = _read_skill("ko")
        for step in range(1, 7):
            pattern = f"{step}단계:"
            assert pattern in content, f"Step {step} missing in Korean"

    def test_steps_present_japanese(self):
        content = _read_skill("jp")
        for step in range(1, 7):
            pattern = f"ステップ{step}:"
            assert pattern in content, f"Step {step} missing in Japanese"


class TestCrushReadsPersonas:
    """Test that crush SKILL references persona files."""

    def test_personas_dir_referenced(self):
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            assert ".honne/personas" in content, \
                f".honne/personas missing in SKILL ({locale})"

    def test_persona_files_referenced(self):
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            assert "antipattern.md" in content, f"antipattern.md missing in SKILL ({locale})"
            assert "signature.md" in content, f"signature.md missing in SKILL ({locale})"
            assert "judge.md" in content, f"judge.md missing in SKILL ({locale})"


class TestCrushNoFileWrites:
    """Test that crush SKILL does not write files (transcript is ephemeral)."""

    def test_no_write_tool_in_crush(self):
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            lines = content.split("\n")
            in_bash_block = False
            for line_no, line in enumerate(lines, 1):
                if line.strip() == "```bash":
                    in_bash_block = True
                    continue
                if in_bash_block and line.strip() == "```":
                    in_bash_block = False
                    continue
                if in_bash_block:
                    # Bash shouldn't have > redirects (file writes)
                    assert " > " not in line and not line.strip().endswith(">"), \
                        f"File redirect in bash block ({locale}), line {line_no}: {line!r}"
            assert "Write tool" not in content, \
                f"Write tool referenced in crush SKILL ({locale})"


class TestCrushOutputFormat:
    """Test that crush SKILL describes output format correctly."""

    def test_output_format_documented(self):
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            # Should mention transcript or output
            assert "Transcript" in content or "出力" in content or "출력" in content or "Output" in content, \
                f"Output format not documented in SKILL ({locale})"
            # Should mention no file writes
            assert "ephemeral" in content or "no file" in content or "ファイル書き込みなし" in content or "파일 쓰기 없음" in content, \
                f"No-file-writes constraint missing in SKILL ({locale})"
