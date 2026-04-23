import json
import pytest
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.render import render_persona, render_report


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test files."""
    return tmp_path


class TestRenderPersona:
    """Test render_persona function."""

    def test_persona_golden_ko(self, temp_dir):
        """Golden test: ko locale with fixed fixture."""
        claims_file = temp_dir / "claims.jsonl"
        persona_file = temp_dir / "persona.json"

        # Fixture input
        claims_data = {
            "id": "c001",
            "type": "claim",
            "axis": "lexicon",
            "scope": "repo",
            "run_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "claim": "자주 쓰는 표현: foo(12), bar(8), baz(5)",
            "support_count": 3,
            "prior_id": None,
            "quotes": [
                {"session_id": "s0000001", "ts": "2025-12-01T10:00:00Z", "text": "foo bar baz", "frequency": 12, "key": "foo"},
                {"session_id": "s0000002", "ts": "2025-12-02T10:00:00Z", "text": "bar baz", "frequency": 8, "key": "bar"},
                {"session_id": "s0000003", "ts": "2025-12-03T10:00:00Z", "text": "baz only", "frequency": 5, "key": "baz"},
            ],
            "created_at": "2025-12-31T23:59:59Z",
        }
        claims_file.write_text(json.dumps(claims_data) + "\n", encoding="utf-8")

        # Render
        result = render_persona(
            claims_path=claims_file,
            scope="repo",
            locale="ko",
            run_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
        )
        assert result == 0
        assert persona_file.exists()

        # Verify determinism (same input → same output)
        persona_data = json.loads(persona_file.read_text(encoding="utf-8"))
        assert persona_data["axes"]["lexicon"]["claim"] == "자주 쓰는 표현: foo(12), bar(8), baz(5)"
        assert len(persona_data["axes"]["lexicon"]["quotes"]) == 3
        assert persona_data["axes"]["lexicon"]["evidence_strength"] == 1.0

        # Re-render and verify byte-identical
        persona_file.unlink()
        result = render_persona(
            claims_path=claims_file,
            scope="repo",
            locale="ko",
            run_id="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
        )
        assert result == 0
        persona_data2 = json.loads(persona_file.read_text(encoding="utf-8"))
        # Verify sorted output (deterministic)
        assert json.dumps(persona_data, sort_keys=True, separators=(',', ':')) == \
               json.dumps(persona_data2, sort_keys=True, separators=(',', ':'))

    def test_persona_missing_claims(self, temp_dir):
        """Missing claims file → exit 1."""
        missing_file = temp_dir / "nonexistent.jsonl"
        persona_file = temp_dir / "persona.json"
        result = render_persona(
            claims_path=missing_file,
            scope="repo",
            locale="ko",
            run_id="test-id",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
        )
        assert result == 1

    def test_persona_all_null(self, temp_dir):
        """Empty claims file → all axes null."""
        claims_file = temp_dir / "claims.jsonl"
        persona_file = temp_dir / "persona.json"
        claims_file.write_text("", encoding="utf-8")

        result = render_persona(
            claims_path=claims_file,
            scope="repo",
            locale="ko",
            run_id="test-id",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
        )
        assert result == 0
        persona_data = json.loads(persona_file.read_text(encoding="utf-8"))
        for axis in ["lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern"]:
            assert persona_data["axes"][axis] is None

    def test_persona_run_id_mismatch(self, temp_dir):
        """Records without matching run_id → filtered out."""
        claims_file = temp_dir / "claims.jsonl"
        persona_file = temp_dir / "persona.json"

        # Old record without run_id
        old_record = {
            "id": "old",
            "type": "claim",
            "axis": "lexicon",
            "scope": "repo",
            "claim": "old claim",
            "created_at": "2025-01-01T00:00:00Z",
        }
        claims_file.write_text(json.dumps(old_record) + "\n", encoding="utf-8")

        result = render_persona(
            claims_path=claims_file,
            scope="repo",
            locale="ko",
            run_id="current-run-id",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
        )
        assert result == 0
        persona_data = json.loads(persona_file.read_text(encoding="utf-8"))
        assert persona_data["axes"]["lexicon"] is None

    def test_persona_with_narrative(self, temp_dir):
        """Narrative inject → explanation + oneliner added to persona."""
        claims_file = temp_dir / "claims.jsonl"
        narrative_file = temp_dir / "narrative.json"
        persona_file = temp_dir / "persona.json"

        claims_data = {
            "id": "c001",
            "type": "claim",
            "axis": "lexicon",
            "scope": "repo",
            "run_id": "test-run",
            "claim": "keyword pattern",
            "quotes": [{"session_id": "s1", "ts": "2025-01-01T00:00:00Z", "text": "foo", "frequency": 1, "key": "foo"}],
            "created_at": "2025-01-01T00:00:00Z",
        }
        claims_file.write_text(json.dumps(claims_data) + "\n", encoding="utf-8")

        narrative_data = {
            "axes": {
                "lexicon": "This is a lexicon explanation",
                "reaction": None,
                "workflow": None,
                "obsession": None,
                "ritual": None,
                "antipattern": None,
            },
            "oneliner": "A concise summary"
        }
        narrative_file.write_text(json.dumps(narrative_data, ensure_ascii=False), encoding="utf-8")

        result = render_persona(
            claims_path=claims_file,
            scope="repo",
            locale="ko",
            run_id="test-run",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
            narrative_path=narrative_file,
        )
        assert result == 0
        persona_data = json.loads(persona_file.read_text(encoding="utf-8"))
        assert persona_data["axes"]["lexicon"]["explanation"] == "This is a lexicon explanation"
        assert persona_data["oneliner"] == "A concise summary"

    def test_persona_without_narrative(self, temp_dir):
        """No narrative → explanation/oneliner set to null."""
        claims_file = temp_dir / "claims.jsonl"
        persona_file = temp_dir / "persona.json"

        claims_data = {
            "id": "c001",
            "type": "claim",
            "axis": "lexicon",
            "scope": "repo",
            "run_id": "test-run",
            "claim": "test claim",
            "quotes": [{"session_id": "s1", "ts": "2025-01-01T00:00:00Z", "text": "foo", "frequency": 1, "key": "foo"}],
            "created_at": "2025-01-01T00:00:00Z",
        }
        claims_file.write_text(json.dumps(claims_data) + "\n", encoding="utf-8")

        result = render_persona(
            claims_path=claims_file,
            scope="repo",
            locale="ko",
            run_id="test-run",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
        )
        assert result == 0
        persona_data = json.loads(persona_file.read_text(encoding="utf-8"))
        assert persona_data["axes"]["lexicon"]["explanation"] is None
        assert persona_data["oneliner"] is None

    def test_persona_narrative_corrupt(self, temp_dir):
        """Corrupt narrative JSON → fallback null, exit 0."""
        claims_file = temp_dir / "claims.jsonl"
        narrative_file = temp_dir / "narrative.json"
        persona_file = temp_dir / "persona.json"

        claims_data = {
            "id": "c001",
            "type": "claim",
            "axis": "lexicon",
            "scope": "repo",
            "run_id": "test-run",
            "claim": "test",
            "quotes": [{"session_id": "s1", "ts": "2025-01-01T00:00:00Z", "text": "foo", "frequency": 1, "key": "foo"}],
            "created_at": "2025-01-01T00:00:00Z",
        }
        claims_file.write_text(json.dumps(claims_data) + "\n", encoding="utf-8")
        narrative_file.write_text("{not valid json", encoding="utf-8")

        result = render_persona(
            claims_path=claims_file,
            scope="repo",
            locale="ko",
            run_id="test-run",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
            narrative_path=narrative_file,
        )
        assert result == 0  # Should still succeed
        persona_data = json.loads(persona_file.read_text(encoding="utf-8"))
        assert persona_data["axes"]["lexicon"]["explanation"] is None
        assert persona_data["oneliner"] is None

    def test_persona_narrative_unknown_axis_dropped(self, temp_dir):
        """Narrative with unknown axis keys → silently drop."""
        claims_file = temp_dir / "claims.jsonl"
        narrative_file = temp_dir / "narrative.json"
        persona_file = temp_dir / "persona.json"

        claims_data = {
            "id": "c001",
            "type": "claim",
            "axis": "lexicon",
            "scope": "repo",
            "run_id": "test-run",
            "claim": "test",
            "quotes": [{"session_id": "s1", "ts": "2025-01-01T00:00:00Z", "text": "foo", "frequency": 1, "key": "foo"}],
            "created_at": "2025-01-01T00:00:00Z",
        }
        claims_file.write_text(json.dumps(claims_data) + "\n", encoding="utf-8")

        narrative_data = {
            "axes": {
                "lexicon": "lexicon explanation",
                "unknown_axis": "should be dropped",
                "reaction": None,
                "workflow": None,
                "obsession": None,
                "ritual": None,
                "antipattern": None,
            },
            "oneliner": "summary"
        }
        narrative_file.write_text(json.dumps(narrative_data), encoding="utf-8")

        result = render_persona(
            claims_path=claims_file,
            scope="repo",
            locale="ko",
            run_id="test-run",
            now="2026-01-01T00:00:00Z",
            out_path=persona_file,
            narrative_path=narrative_file,
        )
        assert result == 0
        persona_data = json.loads(persona_file.read_text(encoding="utf-8"))
        assert persona_data["axes"]["lexicon"]["explanation"] == "lexicon explanation"
        assert "unknown_axis" not in persona_data["axes"]  # Silently dropped


class TestRenderReport:
    """Test render_report function."""

    def test_report_golden_ko(self, temp_dir):
        """Golden report output (ko locale)."""
        persona_file = temp_dir / "persona.json"
        report_file = temp_dir / "report.md"

        persona_data = {
            "generated_at": "2026-01-01T00:00:00Z",
            "scope": "repo",
            "locale": "ko",
            "run_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            "axes": {
                "lexicon": {
                    "claim": "자주 쓰는 표현: foo(12), bar(8)",
                    "quotes": [
                        {"session_id": "s0001", "ts": "2025-12-01T10:00:00Z", "text": "foo text", "frequency": 12},
                        {"session_id": "s0002", "ts": "2025-12-02T10:00:00Z", "text": "bar text", "frequency": 8},
                    ],
                    "evidence_strength": 0.67,
                    "run_ts": "2025-12-31T23:59:59Z",
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
        assert report_file.exists()

        content = report_file.read_text(encoding="utf-8")
        assert "# honne — 자기관찰 보고서" in content
        assert "자주 쓰는 표현: foo(12), bar(8)" in content
        assert "[근거 부족]" in content

    def test_report_missing_persona(self, temp_dir):
        """Missing persona file → exit 1."""
        report_file = temp_dir / "report.md"
        result = render_report(
            persona_path=temp_dir / "nonexistent.json",
            locale="ko",
            out_path=report_file,
        )
        assert result == 1

    def test_report_insufficient_evidence(self, temp_dir):
        """Null axes → [insufficient evidence] rendered."""
        persona_file = temp_dir / "persona.json"
        report_file = temp_dir / "report.md"

        persona_data = {
            "generated_at": "2026-01-01T00:00:00Z",
            "scope": "repo",
            "locale": "ko",
            "run_id": "test-id",
            "axes": {axis: None for axis in ["lexicon", "reaction", "workflow", "obsession", "ritual", "antipattern"]},
        }
        persona_file.write_text(json.dumps(persona_data), encoding="utf-8")

        result = render_report(
            persona_path=persona_file,
            locale="ko",
            out_path=report_file,
        )
        assert result == 0
        content = report_file.read_text(encoding="utf-8")
        assert content.count("[근거 부족]") >= 6  # All axes marked insufficient


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "render"
RUN_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
NOW = "2026-01-01T00:00:00Z"


class TestGoldenFixtures:
    """Byte-identical golden comparisons against checked-in fixtures."""

    @pytest.mark.parametrize("case,locale", [
        ("case_ko", "ko"), ("case_en", "en"),
        ("case_jp", "jp"), ("case_edge", "ko"),
    ])
    def test_persona_golden(self, case, locale, tmp_path):
        out = tmp_path / "persona.json"
        rc = render_persona(
            claims_path=FIXTURE_ROOT / case / "input_claims.jsonl",
            scope="repo", locale=locale, run_id=RUN_ID, now=NOW,
            out_path=out,
        )
        assert rc == 0
        actual = out.read_bytes()
        expected = (FIXTURE_ROOT / case / "expected_persona.json").read_bytes()
        assert actual == expected, f"{case} persona drift"

    @pytest.mark.parametrize("case,locale", [
        ("case_ko", "ko"), ("case_en", "en"),
        ("case_jp", "jp"), ("case_edge", "ko"),
    ])
    def test_report_golden(self, case, locale, tmp_path):
        out = tmp_path / "honne.md"
        rc = render_report(
            persona_path=FIXTURE_ROOT / case / "expected_persona.json",
            locale=locale, out_path=out,
        )
        assert rc == 0
        actual = out.read_bytes()
        expected = (FIXTURE_ROOT / case / "expected_honne.md").read_bytes()
        assert actual == expected, f"{case} report drift"


class TestE2EPipeline:
    """E2E: claims.jsonl → persona.json → honne.md (PRD §6 manual E2E)."""

    @pytest.mark.parametrize("case,locale", [
        ("case_ko", "ko"), ("case_en", "en"),
        ("case_jp", "jp"), ("case_edge", "ko"),
    ])
    def test_pipeline_e2e(self, case, locale, tmp_path):
        persona = tmp_path / "persona.json"
        report = tmp_path / "honne.md"
        rc1 = render_persona(
            claims_path=FIXTURE_ROOT / case / "input_claims.jsonl",
            scope="repo", locale=locale, run_id=RUN_ID, now=NOW,
            out_path=persona,
        )
        assert rc1 == 0 and persona.exists()
        rc2 = render_report(persona_path=persona, locale=locale, out_path=report)
        assert rc2 == 0 and report.exists()
        # Byte-identical to golden at both stages
        assert persona.read_bytes() == (FIXTURE_ROOT / case / "expected_persona.json").read_bytes()
        assert report.read_bytes() == (FIXTURE_ROOT / case / "expected_honne.md").read_bytes()


class TestRenderReportErrors:
    def test_report_bad_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{not json", encoding="utf-8")
        rc = render_report(persona_path=bad, locale="ko", out_path=tmp_path / "r.md")
        assert rc == 1

    def test_report_missing_template(self, tmp_path):
        persona = tmp_path / "p.json"
        persona.write_text(json.dumps({
            "generated_at": NOW, "scope": "repo", "locale": "xx",
            "run_id": RUN_ID,
            "axes": {a: None for a in ["lexicon","reaction","workflow","obsession","ritual","antipattern"]},
        }), encoding="utf-8")
        rc = render_report(persona_path=persona, locale="xx", out_path=tmp_path / "r.md")
        assert rc == 1
