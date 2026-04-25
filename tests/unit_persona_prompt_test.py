"""Unit tests for persona_prompt — build_conflict_payload + render_personas + persona check CLI."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from honne_py.persona_prompt import build_conflict_payload, render_personas
from honne_py.cli import main as cli_main


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


class TestRenderPersonas:
    """Test render_personas with various inputs."""

    def test_render_both_personas(self, tmp_path):
        """Test successful render with both personas + judge."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 0
        assert (out_dir / "antipattern.md").exists()
        assert (out_dir / "signature.md").exists()
        assert (out_dir / "judge.md").exists()

        # Check content
        antipattern_content = (out_dir / "antipattern.md").read_text(encoding="utf-8")
        assert "과잉명세형" in antipattern_content
        assert "당신은" in antipattern_content

        signature_content = (out_dir / "signature.md").read_text(encoding="utf-8")
        assert "정밀타격형" in signature_content
        assert "당신은" in signature_content

        judge_content = (out_dir / "judge.md").read_text(encoding="utf-8")
        assert "심판자" in judge_content or "판결" in judge_content

    def test_render_antipattern_only(self, tmp_path):
        """Test render with only antipattern (signature null)."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_no_signature.json"
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 0
        assert (out_dir / "antipattern.md").exists()
        assert not (out_dir / "signature.md").exists()
        assert not (out_dir / "judge.md").exists()

    def test_render_signature_only(self, tmp_path):
        """Test render with only signature (antipattern null)."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_no_antipattern.json"
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 0
        assert not (out_dir / "antipattern.md").exists()
        assert (out_dir / "signature.md").exists()
        assert not (out_dir / "judge.md").exists()

    def test_render_both_null(self, tmp_path):
        """Test render with both personas null."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_no_axes.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_no_axes.json"
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 0
        # No files created, but success (nothing to render)
        assert not (out_dir / "antipattern.md").exists()
        assert not (out_dir / "signature.md").exists()
        assert not (out_dir / "judge.md").exists()

    def test_missing_conflict_present_key(self, tmp_path):
        """Test synthesis missing 'conflict_present' key."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = tmp_path / "bad.json"
        synthesis_path.write_text(json.dumps({
            "persona_antipattern": {"name": "x", "oneliner": "y", "system_prompt": "z"}
        }))
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 66

    def test_conflict_true_missing_persona_block(self, tmp_path):
        """Test conflict_present=true but required persona block missing."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = tmp_path / "bad.json"
        synthesis_path.write_text(json.dumps({
            "conflict_present": True,
            "persona_antipattern": {"name": "x", "oneliner": "y", "system_prompt": "z"},
            "persona_signature": None,
            "judge_system_prompt": "judge"
        }))
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 66

    def test_persona_block_missing_name(self, tmp_path):
        """Test persona block missing 'name' field."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = tmp_path / "bad.json"
        synthesis_path.write_text(json.dumps({
            "conflict_present": True,
            "persona_antipattern": {"oneliner": "y", "system_prompt": "z"},  # missing name
            "persona_signature": {"name": "x", "oneliner": "y", "system_prompt": "z"},
            "judge_system_prompt": "judge"
        }))
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 66

    def test_all_three_locales(self, tmp_path):
        """Test that render works with all three supported locales."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"

        for locale in ["ko", "en", "jp"]:
            out_dir = tmp_path / f"personas_{locale}"
            rc = render_personas(synthesis_path, persona_path, locale, out_dir)
            assert rc == 0, f"Failed for locale {locale}"
            assert (out_dir / "antipattern.md").exists()
            assert (out_dir / "signature.md").exists()

    def test_missing_synthesis_file(self, tmp_path):
        """Test when synthesis file does not exist."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = tmp_path / "nonexistent.json"
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 66

    def test_missing_persona_file(self, tmp_path):
        """Test when persona file does not exist."""
        persona_path = tmp_path / "nonexistent.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_dir = tmp_path / "personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 66

    def test_missing_template(self, tmp_path):
        """Test when template for locale does not exist."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_dir = tmp_path / "personas"

        # Try with a locale that has no template (not ko, en, or jp)
        rc = render_personas(synthesis_path, persona_path, "invalid", out_dir)

        assert rc == 2

    def test_output_dir_created(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        synthesis_path = Path(__file__).parent / "fixtures/persona/synthesis_full.json"
        out_dir = tmp_path / "deep/nested/dir/personas"

        rc = render_personas(synthesis_path, persona_path, "ko", out_dir)

        assert rc == 0
        assert out_dir.exists()


class TestPersonaCheckCLI:
    """Unit tests for 'honne persona check' CLI subcommand."""

    def test_persona_check_exists(self):
        persona_path = Path(__file__).parent / "fixtures/persona/persona_full.json"
        rc = cli_main(["persona", "check", "--persona", str(persona_path)])
        assert rc == 0

    def test_persona_check_missing(self, tmp_path):
        persona_path = tmp_path / "nonexistent.json"
        rc = cli_main(["persona", "check", "--persona", str(persona_path)])
        assert rc == 66
