import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.axis import collect_quotes


class TestEmptyQuoteGuard:
    """Test empty quote guard in collect_quotes."""

    def test_collect_quotes_drops_blank_text(self, tmp_path):
        """Empty/whitespace text is dropped from results."""
        scan_file = tmp_path / "scan.json"

        # Scan with messages containing empty text
        scan_data = {
            "sessions": [
                {
                    "session_id": "s001",
                    "started_at": "2025-01-01T00:00:00Z",
                    "messages": [
                        {"role": "user", "text": "foo"},  # normal
                        {"role": "user", "text": "   "},  # whitespace only
                        {"role": "user", "text": ""},     # empty
                        {"role": "user", "text": "bar"},  # normal
                    ],
                }
            ]
        }
        scan_file.write_text(json.dumps(scan_data), encoding="utf-8")

        # Signal with candidates including empty keys
        signal = {
            "counters": {
                "foo": 5,
                "bar": 3,
            }
        }

        # collect_quotes should skip empty text matches
        quotes = collect_quotes(scan_file, "reaction", signal, k=3)

        # Verify empty quotes are not in results
        for quote in quotes:
            assert quote["text"].strip(), f"Found empty quote: {quote}"

    def test_empty_quote_in_direct_axes(self, tmp_path):
        """Empty text in workflow/antipattern/ritual (direct axes)."""
        scan_file = tmp_path / "scan.json"
        scan_file.write_text(json.dumps({"sessions": []}), encoding="utf-8")

        # _DIRECT_AXES path: first_text empty → skip
        signal = {
            "counters": {"step1": 5},
            "top_examples": [
                {"first_text": "   ", "first_session_id": "s1", "first_ts": "2025-01-01T00:00:00Z", "key": "step1"},
                {"first_text": "real step", "first_session_id": "s2", "first_ts": "2025-01-02T00:00:00Z", "key": "step2"},
            ]
        }

        quotes = collect_quotes(scan_file, "workflow", signal, k=3)

        # Whitespace-only first_text should be skipped
        for quote in quotes:
            assert quote["text"].strip(), f"Found whitespace quote: {quote}"

    def test_empty_quote_in_obsession(self, tmp_path):
        """Empty text in obsession (top_preambles)."""
        scan_file = tmp_path / "scan.json"
        scan_file.write_text(json.dumps({"sessions": []}), encoding="utf-8")

        signal = {
            "top_preambles": [
                {"text": "", "first_session_id": "s1", "first_ts": "2025-01-01T00:00:00Z", "count": 3},
                {"text": "real preamble", "first_session_id": "s2", "first_ts": "2025-01-02T00:00:00Z", "count": 2},
            ]
        }

        quotes = collect_quotes(scan_file, "obsession", signal, k=3)

        # Empty text should be skipped
        for quote in quotes:
            assert quote["text"].strip()

    def test_no_empty_bullets_in_render(self, tmp_path):
        """_render_block should not contain empty bullet lines."""
        from honne_py.axis import _render_block

        # Load a template mock
        out_dict = {
            "axis": "lexicon",
            "quotes": [
                {"session_id": "s1", "ts": "2025-01-01T10:00:00Z", "text": "normal quote", "frequency": 5, "key": "test"},
                # Empty text should already be filtered out by collect_quotes
            ],
            "candidate_claim": "test claim",
            "insufficient_evidence": False,
        }

        template = {
            "report_header": "축 1 — 어휘",
            "hitl_question": "수용?",
            "connective": " · ",
        }

        block = _render_block(out_dict, template)

        # Verify no empty bullet lines
        for line in block.split("\n"):
            if line.startswith("- "):
                # Bullet line should not be empty after dash
                assert line.strip() != "-"
