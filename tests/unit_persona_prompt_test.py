"""Unit tests for persona_prompt — build_conflict_payload + render_persona_prompt."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from honne_py.persona_prompt import build_conflict_payload, render_persona_prompt


class TestBuildConflictPayload:
    """Test build_conflict_payload with various input states."""

    def test_both_axes_present(self):
        """Test with both antipattern and signature present."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        payload = build_conflict_payload(persona_path, "ko")

        assert payload["locale"] == "ko"
        assert payload["antipattern"] is not None
        assert payload["antipattern"]["claim"] == "비효율 패턴: overspec(251), repeat_same_request(82)"
        assert payload["signature"] is not None
        assert payload["signature"]["claim"] == "시그니처 패턴: targeted_request(573), decisive_close(225)"
        assert "supporting_axes" in payload
        assert "lexicon" in payload["supporting_axes"]

    def test_antipattern_null(self):
        """Test with antipattern absent (null claim)."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_no_antipattern.json"
        payload = build_conflict_payload(persona_path, "ko")

        assert payload["antipattern"] is None
        assert payload["signature"] is not None
        assert payload["signature"]["claim"] == "시그니처 패턴: targeted_request(573), decisive_close(225)"

    def test_invalid_locale(self, tmp_path):
        """Test with invalid locale."""
        persona_path = tmp_path / "test.json"
        persona_path.write_text(json.dumps({
            "axes": {
                "antipattern": {"claim": "test"},
                "signature": {"claim": "test"}
            }
        }))

        with pytest.raises(SystemExit) as exc_info:
            build_conflict_payload(persona_path, "invalid")
        assert exc_info.value.code == 2

    def test_missing_persona_file(self):
        """Test when persona.json does not exist."""
        with pytest.raises(SystemExit) as exc_info:
            build_conflict_payload(Path("/nonexistent/persona.json"), "ko")
        assert exc_info.value.code == 66

    def test_supporting_axes_included(self):
        """Test that all 5 supporting axes are included in payload."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        payload = build_conflict_payload(persona_path, "ko")

        supporting = payload["supporting_axes"]
        expected_axes = {"lexicon", "reaction", "workflow", "obsession", "ritual"}
        assert expected_axes.issubset(supporting.keys())

        for axis in expected_axes:
            assert supporting[axis]["claim"] is not None
            assert "evidence_strength" in supporting[axis]

    def test_both_axes_null(self):
        """Test with both antipattern and signature absent (portrait mode)."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_no_axes.json"
        payload = build_conflict_payload(persona_path, "ko")

        assert payload["antipattern"] is None
        assert payload["signature"] is None
        assert payload["conflict_present"] is False  # portrait mode
        # Supporting axes still populated
        supporting = payload["supporting_axes"]
        assert len(supporting) >= 5


class TestRenderPersonaPrompt:
    """Test render_persona_prompt with various inputs."""

    def test_render_full(self, tmp_path):
        """Test successful render with both axes present — must include debate + activation directive."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_path = tmp_path / "persona-prompt.md"

        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 0
        assert out_path.exists()

        content = out_path.read_text(encoding="utf-8")
        assert "범위수렴형" in content  # character_oneliner
        assert "당신은" in content  # "Who you are" section
        assert "시그니처 패턴" in content
        assert "주의할 점" in content
        assert "시스템 프롬프트" in content
        # debate section rendered
        assert "내면의 충돌" in content
        assert "antipattern" in content
        assert "signature" in content
        # activation directive rendered
        assert "활성화 지시" in content
        assert "중립적 Claude로 돌아가지" in content

    def test_render_missing_debate_when_conflict_true(self, tmp_path):
        """conflict_present=true but debate missing → exit 66."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = tmp_path / "bad.json"
        synthesis_path.write_text(json.dumps({
            "verdict": "x",
            "character_oneliner": "y",
            "system_prompt": "z",
            "conflict_present": True
        }))
        out_path = tmp_path / "out.md"
        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)
        assert rc == 66

    def test_render_partial_debate_rejected(self, tmp_path):
        """conflict_present=true with incomplete debate → exit 66."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = tmp_path / "bad.json"
        synthesis_path.write_text(json.dumps({
            "verdict": "x",
            "character_oneliner": "y",
            "system_prompt": "z",
            "conflict_present": True,
            "debate": {"antipattern_voice": "a"}
        }))
        out_path = tmp_path / "out.md"
        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)
        assert rc == 66

    def test_render_conflict_false_with_null_debate(self, tmp_path):
        """conflict_present=false with explicit debate:null → render succeeds, debate skipped."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_no_antipattern.json"
        synthesis_path = tmp_path / "ok.json"
        synthesis_path.write_text(json.dumps({
            "verdict": "단일 축 포트레이트",
            "character_oneliner": "정밀 타겟터",
            "system_prompt": "당신은 정밀 타겟터입니다.",
            "conflict_present": False,
            "debate": None
        }))
        out_path = tmp_path / "out.md"
        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)
        assert rc == 0
        content = out_path.read_text(encoding="utf-8")
        assert "내면의 충돌" not in content  # debate section omitted
        assert "활성화 지시" in content       # activation still renders

    def test_render_with_no_antipattern(self, tmp_path):
        """Test render when antipattern is absent."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_no_antipattern.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_path = tmp_path / "persona-prompt.md"

        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 0
        content = out_path.read_text(encoding="utf-8")
        assert "시그니처 패턴" in content
        assert "주의할 점" not in content

    def test_render_with_both_axes_null(self, tmp_path):
        """Test render in portrait mode (both conflict axes absent)."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_no_axes.json"
        synthesis_path = tmp_path / "synthesis.json"
        synthesis_path.write_text(json.dumps({
            "verdict": "지속적 정확성 추구형",
            "character_oneliner": "세심하게 반복하는 사람",
            "system_prompt": "당신은 정확성을 중시합니다.",
            "conflict_present": False
        }))
        out_path = tmp_path / "persona-prompt.md"

        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 0
        content = out_path.read_text(encoding="utf-8")
        assert "주의할 점" not in content   # no antipattern → no watch-out section
        assert "시그니처 패턴" not in content  # no signature → no signature section

    def test_missing_synthesis_file(self, tmp_path):
        """Test when synthesis.json does not exist."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = tmp_path / "nonexistent.json"
        out_path = tmp_path / "out.md"

        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 66

    def test_missing_persona_file(self, tmp_path):
        """Test when persona.json does not exist."""
        persona_path = tmp_path / "nonexistent.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_path = tmp_path / "out.md"

        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 66

    def test_missing_template(self, tmp_path):
        """Test when template for locale does not exist."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_path = tmp_path / "out.md"

        # Try with a locale that has no template (not ko, en, or jp)
        rc = render_persona_prompt(synthesis_path, persona_path, "invalid", out_path)

        assert rc == 2

    def test_output_dir_created(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_path = tmp_path / "deep/nested/dir/persona-prompt.md"

        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 0
        assert out_path.exists()
        assert out_path.parent.exists()

    def test_render_structure(self, tmp_path):
        """Test that output has correct markdown structure."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_path = tmp_path / "persona-prompt.md"

        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 0
        content = out_path.read_text(encoding="utf-8")

        # Check for section headers
        assert "## 당신은" in content or "## Who You Are" in content
        assert "## 시스템 프롬프트" in content or "## System Prompt" in content

        # Check for system prompt delimiters
        assert "---" in content
        lines = content.split('\n')
        delimiter_count = sum(1 for line in lines if line.strip() == "---")
        assert delimiter_count >= 2


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_synthesis_fields(self, tmp_path):
        """Test render with empty fields in synthesis."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"

        synthesis_path = tmp_path / "synthesis.json"
        synthesis_path.write_text(json.dumps({
            "verdict": "",
            "character_oneliner": "",
            "system_prompt": "",
            "conflict_present": False
        }))

        out_path = tmp_path / "out.md"
        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 0
        content = out_path.read_text(encoding="utf-8")
        # Output should still have structure, even with empty content
        assert "## 당신은" in content or "## Who You Are" in content

    def test_malformed_synthesis_json(self, tmp_path):
        """Test with malformed synthesis JSON."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = tmp_path / "bad.json"
        synthesis_path.write_text("{ bad json }")
        out_path = tmp_path / "out.md"

        rc = render_persona_prompt(synthesis_path, persona_path, "ko", out_path)

        assert rc == 66

    def test_all_three_locales(self, tmp_path):
        """Test that render works with all three supported locales."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"

        for locale in ["ko", "en", "jp"]:
            out_path = tmp_path / f"out_{locale}.md"
            rc = render_persona_prompt(synthesis_path, persona_path, locale, out_path)
            assert rc == 0, f"Failed for locale {locale}"
            assert out_path.exists()
