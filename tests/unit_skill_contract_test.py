import re
import pytest
from pathlib import Path


class TestSkillContract:
    """Test SKILL.md contract compliance."""

    def _read_skill_step(self, locale: str, step_num: int) -> str:
        """Read Step N from SKILL.md (locale version)."""
        locale_suffix = f".{locale}" if locale != "en" else ""
        skill_file = Path(__file__).parent.parent / f"skills/whoami/SKILL{locale_suffix}.md"
        content = skill_file.read_text(encoding="utf-8")
        # Extract step content: from step header to next "##" or end
        # Patterns: "## Step N:" (en), "## ステップN:" (jp), "## N단계:" (ko)
        pattern = rf"^## (?:Step {step_num}:|ステップ{step_num}:|{step_num}단계:).*?$\n(.*?)(?=\n^## |\Z)"
        match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1)
        return ""

    def test_skill_no_askuserquestion_in_step4(self):
        """Step 4: no AskUserQuestion calls."""
        for locale in ["en", "ko", "jp"]:
            step4 = self._read_skill_step(locale, 4)
            assert "AskUserQuestion" not in step4, f"Step 4 ({locale}) has AskUserQuestion"

    def test_skill_step4_has_quotes_json_arg(self):
        """Step 4: record claim includes --quotes-json argument."""
        for locale in ["en", "ko", "jp"]:
            step4 = self._read_skill_step(locale, 4)
            assert "--quotes-json" in step4, f"Step 4 ({locale}) missing --quotes-json"

    def test_skill_step5_synthesis_block_present(self):
        """Step 5: LLM synthesis narrative.json generation present."""
        for locale in ["en", "ko", "jp"]:
            step5 = self._read_skill_step(locale, 5)
            assert "narrative.json" in step5, f"Step 5 ({locale}) missing narrative.json"
            assert ".honne/cache/narrative.json" in step5, f"Step 5 ({locale}) wrong narrative path"

    def test_skill_step6_render_has_narrative_arg(self):
        """Step 6: render persona includes --narrative argument."""
        for locale in ["en", "ko", "jp"]:
            step6 = self._read_skill_step(locale, 6)
            assert "--narrative" in step6, f"Step 6 ({locale}) missing --narrative arg"
            assert ".honne/cache/narrative.json" in step6, f"Step 6 ({locale}) wrong narrative path"

    def test_skill_step3_no_hitl_reference(self):
        """Step 3: no 'HITL' wording — Step 4 is autonomous, not HITL."""
        for locale in ["en", "ko", "jp"]:
            step3 = self._read_skill_step(locale, 3)
            assert "HITL" not in step3, f"Step 3 ({locale}) contains stale HITL reference"

    def test_skill_all_locales_exist(self):
        """All 3 SKILL locale files exist."""
        skill_root = Path(__file__).parent.parent / "skills/whoami"
        for locale in ["ko", "en", "jp"]:
            locale_suffix = f".{locale}" if locale != "en" else ""
            skill_file = skill_root / f"SKILL{locale_suffix}.md"
            assert skill_file.exists(), f"SKILL{locale_suffix}.md missing"

    def test_skill_version_match(self):
        """All SKILL files have matching version."""
        skill_root = Path(__file__).parent.parent / "skills/whoami"
        versions = {}
        for locale in ["ko", "en", "jp"]:
            locale_suffix = f".{locale}" if locale != "en" else ""
            skill_file = skill_root / f"SKILL{locale_suffix}.md"
            content = skill_file.read_text(encoding="utf-8")
            match = re.search(r"^version: (.+?)$", content, re.MULTILINE)
            if match:
                versions[locale] = match.group(1)
        # All versions should be the same
        assert len(set(versions.values())) == 1, f"Version mismatch: {versions}"
