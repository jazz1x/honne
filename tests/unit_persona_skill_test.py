"""SKILL.md contract tests for honne:persona skill."""
import json
import re
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).parent.parent / "skills/persona"
PLUGIN_JSON = Path(__file__).parent.parent / ".claude-plugin/plugin.json"


def _read_skill(locale: str) -> str:
    suffix = f".{locale}" if locale != "en" else ""
    path = SKILL_ROOT / f"SKILL{suffix}.md"
    return path.read_text(encoding="utf-8")


def _skill_step(locale: str, step_num: int) -> str:
    content = _read_skill(locale)
    # Patterns: "## Step N:" (en), "## ステップN:" (jp), "## N단계:" (ko)
    pattern = rf"^## (?:Step {step_num}:|ステップ{step_num}:|{step_num}단계:).*?$\n(.*?)(?=\n^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else ""


class TestSkillFilesExist:
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

    def test_name_is_persona(self):
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            m = re.search(r"^name: (.+?)$", content, re.MULTILINE)
            assert m, f"name missing in SKILL ({locale})"
            assert m.group(1).strip() == "persona", f"name not 'persona' in SKILL ({locale})"


class TestSkillStep2:
    def test_check_only_flag_present(self):
        for locale in ["en", "ko", "jp"]:
            step2 = _skill_step(locale, 2)
            assert "--check-only" in step2, f"--check-only missing from Step 2 ({locale})"

    def test_persona_json_path_in_step2(self):
        for locale in ["en", "ko", "jp"]:
            step2 = _skill_step(locale, 2)
            assert ".honne/persona.json" in step2, f".honne/persona.json missing from Step 2 ({locale})"

    def test_exit_66_handling_in_step2(self):
        for locale in ["en", "ko", "jp"]:
            step2 = _skill_step(locale, 2)
            assert "66" in step2, f"Exit 66 handling missing from Step 2 ({locale})"

    def test_staleness_check_present(self):
        for locale in ["en", "ko", "jp"]:
            step2 = _skill_step(locale, 2)
            assert "STALE_DAYS" in step2, f"staleness check missing from Step 2 ({locale})"


class TestSkillStep4:
    def test_persona_synthesis_json_in_step4(self):
        for locale in ["en", "ko", "jp"]:
            step4 = _skill_step(locale, 4)
            assert "persona-synthesis.json" in step4, f"persona-synthesis.json missing from Step 4 ({locale})"

    def test_synthesis_prompt_read_in_step4(self):
        for locale in ["en", "ko", "jp"]:
            step4 = _skill_step(locale, 4)
            assert "persona_synthesis_prompt" in step4, f"synthesis prompt read missing from Step 4 ({locale})"

    def test_conflict_present_mentioned_in_step4(self):
        for locale in ["en", "ko", "jp"]:
            step4 = _skill_step(locale, 4)
            assert "conflict_present" in step4, f"conflict_present missing from Step 4 ({locale})"

    def test_no_heredoc_in_step4(self):
        for locale in ["en", "ko", "jp"]:
            step4 = _skill_step(locale, 4)
            # Actual heredoc syntax inside bash code blocks would start with << on its own line
            # Prose mentions (in backticks) are OK — check for bare heredoc marker
            lines = step4.split("\n")
            in_bash_block = False
            for line in lines:
                if line.strip() == "```bash":
                    in_bash_block = True
                    continue
                if in_bash_block and line.strip() == "```":
                    in_bash_block = False
                    continue
                if in_bash_block:
                    assert not re.match(r"^\s*<<\s*['\"]?EOF", line), \
                        f"heredoc in bash block in Step 4 ({locale}): {line!r}"


class TestSkillStep5:
    def test_persona_prompt_md_in_step5(self):
        for locale in ["en", "ko", "jp"]:
            step5 = _skill_step(locale, 5)
            assert "persona-prompt.md" in step5, f"persona-prompt.md missing from Step 5 ({locale})"

    def test_render_persona_prompt_cmd_in_step5(self):
        for locale in ["en", "ko", "jp"]:
            step5 = _skill_step(locale, 5)
            assert "render persona-prompt" in step5, f"render persona-prompt cmd missing from Step 5 ({locale})"


class TestNoCLAUDEmdInjection:
    def test_no_claude_md_write_in_any_bash_block(self):
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            lines = content.split("\n")
            in_bash_block = False
            for line in lines:
                if line.strip() == "```bash":
                    in_bash_block = True
                    continue
                if in_bash_block and line.strip() == "```":
                    in_bash_block = False
                    continue
                if in_bash_block:
                    assert "CLAUDE.md" not in line, \
                        f"CLAUDE.md referenced in bash block ({locale}): {line!r}"


class TestNoHeredocsInBashBlocks:
    def test_no_heredocs_in_any_bash_block(self):
        for locale in ["en", "ko", "jp"]:
            content = _read_skill(locale)
            lines = content.split("\n")
            in_bash_block = False
            for line in lines:
                if line.strip() == "```bash":
                    in_bash_block = True
                    continue
                if in_bash_block and line.strip() == "```":
                    in_bash_block = False
                    continue
                if in_bash_block:
                    assert not re.match(r".*<<\s*['\"]?(?:EOF|PYEOF)", line), \
                        f"heredoc in bash block ({locale}): {line!r}"


class TestSynthesisPromptTemplates:
    def test_all_locale_templates_exist(self):
        tmpl_dir = SKILL_ROOT / "templates"
        for locale in ["ko", "en", "jp"]:
            tmpl = tmpl_dir / f"persona_synthesis_prompt.{locale}.md"
            assert tmpl.exists(), f"persona_synthesis_prompt.{locale}.md missing"

    def test_templates_have_system_section(self):
        tmpl_dir = SKILL_ROOT / "templates"
        for locale in ["ko", "en", "jp"]:
            tmpl = tmpl_dir / f"persona_synthesis_prompt.{locale}.md"
            content = tmpl.read_text(encoding="utf-8")
            assert "# system" in content, f"# system section missing in synthesis prompt ({locale})"

    def test_templates_have_three_branches(self):
        tmpl_dir = SKILL_ROOT / "templates"
        for locale in ["ko", "en", "jp"]:
            tmpl = tmpl_dir / f"persona_synthesis_prompt.{locale}.md"
            content = tmpl.read_text(encoding="utf-8")
            assert "conflict_present" in content, f"conflict_present missing in synthesis prompt ({locale})"

    def test_templates_have_debate_contract(self):
        """All synthesis templates must reference the debate schema keys."""
        tmpl_dir = SKILL_ROOT / "templates"
        required_keys = ["debate", "antipattern_voice", "signature_voice", "resolution"]
        for locale in ["ko", "en", "jp"]:
            tmpl = tmpl_dir / f"persona_synthesis_prompt.{locale}.md"
            content = tmpl.read_text(encoding="utf-8")
            for key in required_keys:
                assert key in content, f"debate contract key '{key}' missing in synthesis prompt ({locale})"

    def test_templates_forbid_invented_claims(self):
        tmpl_dir = SKILL_ROOT / "templates"
        for locale in ["ko", "en", "jp"]:
            tmpl = tmpl_dir / f"persona_synthesis_prompt.{locale}.md"
            content = tmpl.read_text(encoding="utf-8")
            # Each template must have an explicit prohibition against inventing behavioral claims
            forbidden_keywords = ["invent", "fabricat", "발명", "만들지", "창작", "捏造", "でっち上げ"]
            has_prohibition = any(kw in content for kw in forbidden_keywords)
            assert has_prohibition, \
                f"synthesis prompt ({locale}) missing explicit prohibition against inventing claims"

    def test_templates_mention_token_limit(self):
        tmpl_dir = SKILL_ROOT / "templates"
        for locale in ["ko", "en", "jp"]:
            tmpl = tmpl_dir / f"persona_synthesis_prompt.{locale}.md"
            content = tmpl.read_text(encoding="utf-8")
            assert "1500" in content, f"1500 token limit not mentioned in synthesis prompt ({locale})"


class TestWhoamiSkillNoTmpWrites:
    def test_no_tmp_writes_in_whoami_bash_blocks(self):
        """Verify that whoami SKILL.md files don't write to /tmp.

        Hardening requirement: all intermediate data must go to .honne/cache/,
        not /tmp. This test enforces the contract across all locales.
        """
        whoami_skill_root = Path(__file__).parent.parent / "skills/whoami"
        for locale in ["en", "ko", "jp"]:
            suffix = f".{locale}" if locale != "en" else ""
            skill_path = whoami_skill_root / f"SKILL{suffix}.md"
            assert skill_path.exists(), f"SKILL{suffix}.md missing in skills/whoami"

            content = skill_path.read_text(encoding="utf-8")
            lines = content.split("\n")
            in_bash_block = False

            for line_no, line in enumerate(lines, 1):
                if line.strip() == "```bash":
                    in_bash_block = True
                    continue
                if in_bash_block and line.strip() == "```":
                    in_bash_block = False
                    continue
                if in_bash_block and "/tmp" in line:
                    assert False, \
                        f"whoami SKILL{suffix}.md:{line_no} — /tmp write in bash block (use .honne/cache/ instead): {line!r}"


class TestPluginJson:
    def test_plugin_json_exists(self):
        assert PLUGIN_JSON.exists(), ".claude-plugin/plugin.json not found"

    def test_plugin_json_valid(self):
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        assert "name" in data
        assert "version" in data
        assert "skills" in data

    def test_plugin_json_version_0_0_2(self):
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        assert data["version"] == "0.0.2", f"Expected version 0.0.2, got {data['version']}"

    def test_skills_directory_pointer(self):
        data = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
        assert data["skills"] == "./skills", "skills pointer should be './skills'"
