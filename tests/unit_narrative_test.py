import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.render import render_report


class TestNarrativeRender:
    """Test narrative explanation + footer rendering."""

    def test_narrative_render_axis_explanation(self, tmp_path):
        """Persona with explanation → axis_block includes explanation line."""
        persona_file = tmp_path / "persona.json"
        report_file = tmp_path / "report.md"

        persona_data = {
            "generated_at": "2026-01-01T00:00:00Z",
            "scope": "repo",
            "locale": "ko",
            "run_id": "test-id",
            "oneliner": None,
            "axes": {
                "lexicon": {
                    "claim": "키워드 반복 사용",
                    "explanation": "특정 키워드 반복 패턴",
                    "quotes": [{"session_id": "s1", "ts": "2025-01-01T00:00:00Z", "text": "foo", "frequency": 1}],
                    "evidence_strength": 0.33,
                    "run_ts": "2025-01-01T00:00:00Z",
                },
                "reaction": None,
                "workflow": None,
                "obsession": None,
                "ritual": None,
                "antipattern": None,
            },
        }
        persona_file.write_text(json.dumps(persona_data, ensure_ascii=False), encoding="utf-8")

        result = render_report(
            persona_path=persona_file,
            locale="ko",
            out_path=report_file,
        )
        assert result == 0
        content = report_file.read_text(encoding="utf-8")
        assert "**해설**: 특정 키워드 반복 패턴" in content

    def test_narrative_render_axis_explanation_null(self, tmp_path):
        """Persona with explanation=null → explanation line absent."""
        persona_file = tmp_path / "persona.json"
        report_file = tmp_path / "report.md"

        persona_data = {
            "generated_at": "2026-01-01T00:00:00Z",
            "scope": "repo",
            "locale": "ko",
            "run_id": "test-id",
            "oneliner": None,
            "axes": {
                "lexicon": {
                    "claim": "키워드 반복 사용",
                    "explanation": None,
                    "quotes": [{"session_id": "s1", "ts": "2025-01-01T00:00:00Z", "text": "foo", "frequency": 1}],
                    "evidence_strength": 0.33,
                    "run_ts": "2025-01-01T00:00:00Z",
                },
                "reaction": None,
                "workflow": None,
                "obsession": None,
                "ritual": None,
                "antipattern": None,
            },
        }
        persona_file.write_text(json.dumps(persona_data, ensure_ascii=False), encoding="utf-8")

        result = render_report(
            persona_path=persona_file,
            locale="ko",
            out_path=report_file,
        )
        assert result == 0
        content = report_file.read_text(encoding="utf-8")
        assert "**해설**:" not in content

    def test_narrative_render_footer_with_oneliner(self, tmp_path):
        """Persona with oneliner → footer section rendered."""
        persona_file = tmp_path / "persona.json"
        report_file = tmp_path / "report.md"

        persona_data = {
            "generated_at": "2026-01-01T00:00:00Z",
            "scope": "repo",
            "locale": "ko",
            "run_id": "test-id",
            "oneliner": "한 줄 평가",
            "axes": {axis: None for axis in ["lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern"]},
        }
        persona_file.write_text(json.dumps(persona_data, ensure_ascii=False), encoding="utf-8")

        result = render_report(
            persona_path=persona_file,
            locale="ko",
            out_path=report_file,
        )
        assert result == 0
        content = report_file.read_text(encoding="utf-8")
        assert "## 종합 분석" in content
        assert "한 줄 평가" in content

    def test_narrative_render_footer_null(self, tmp_path):
        """Persona with oneliner=null → footer section absent."""
        persona_file = tmp_path / "persona.json"
        report_file = tmp_path / "report.md"

        persona_data = {
            "generated_at": "2026-01-01T00:00:00Z",
            "scope": "repo",
            "locale": "ko",
            "run_id": "test-id",
            "oneliner": None,
            "axes": {axis: None for axis in ["lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern"]},
        }
        persona_file.write_text(json.dumps(persona_data, ensure_ascii=False), encoding="utf-8")

        result = render_report(
            persona_path=persona_file,
            locale="ko",
            out_path=report_file,
        )
        assert result == 0
        content = report_file.read_text(encoding="utf-8")
        assert "## 종합 분석" not in content

    def test_next_actions_always_rendered(self, tmp_path):
        """next_actions section renders regardless of oneliner presence."""
        for has_oneliner in [True, False]:
            persona_file = tmp_path / f"persona_{has_oneliner}.json"
            report_file = tmp_path / f"report_{has_oneliner}.md"
            persona_data = {
                "generated_at": "2026-01-01T00:00:00Z",
                "scope": "repo", "locale": "ko", "run_id": "test-id",
                "oneliner": "테스트 분석" if has_oneliner else None,
                "axes": {a: None for a in ["lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern"]},
            }
            persona_file.write_text(json.dumps(persona_data, ensure_ascii=False), encoding="utf-8")
            result = render_report(persona_path=persona_file, locale="ko", out_path=report_file)
            assert result == 0
            content = report_file.read_text(encoding="utf-8")
            assert "다음 액션 제안" in content, f"next_actions missing when oneliner={has_oneliner}"
            assert "추가될 예정" in content


class TestTemplateStructure:
    """Test synthesis_prompt and report template structure."""

    def test_narrative_template_synthesis_prompt_3_locales(self):
        """All 3 synthesis_prompt files exist with system/user markers."""
        template_root = Path(__file__).parent.parent / "skills/whoami/templates"
        for locale in ["ko", "en", "jp"]:
            prompt_file = template_root / f"synthesis_prompt.{locale}.md"
            assert prompt_file.exists(), f"synthesis_prompt.{locale}.md missing"
            content = prompt_file.read_text(encoding="utf-8")
            assert "# system" in content, f"synthesis_prompt.{locale}.md missing # system section"
            assert "# user" in content, f"synthesis_prompt.{locale}.md missing # user section"

    def test_report_template_has_footer(self):
        """All 3 report templates have footer section."""
        template_root = Path(__file__).parent.parent / "skills/whoami/templates"
        for locale in ["ko", "en", "jp"]:
            report_file = template_root / f"report.{locale}.md"
            assert report_file.exists(), f"report.{locale}.md missing"
            content = report_file.read_text(encoding="utf-8")
            assert "## footer" in content, f"report.{locale}.md missing ## footer section"
            assert "## axis_block" in content, f"report.{locale}.md missing ## axis_block section"
