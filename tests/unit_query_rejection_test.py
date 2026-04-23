import pytest
import json
import sys
from pathlib import Path
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.query import query


class TestQueryRejectionMissingFiles:
    """Test query fallback for missing files."""

    def test_missing_base_dir_returns_empty(self, tmp_path, capsys):
        """Missing base_dir → exit 0, empty JSON []."""
        missing_dir = tmp_path / "nonexistent"

        result = query(
            base_dir=missing_dir,
            scope="repo",
            type_="rejection",
        )
        assert result == 0
        captured = capsys.readouterr()
        # Should print empty list
        assert "[]" in captured.out

    def test_missing_rejections_file(self, tmp_path, capsys):
        """Missing rejections.jsonl but assets dir exists → exit 0, []."""
        base_dir = tmp_path / ".honne"
        asset_dir = base_dir / "assets"
        asset_dir.mkdir(parents=True)

        # Create claims.jsonl but not rejections.jsonl
        (asset_dir / "claims.jsonl").write_text('{"id":"c1","type":"claim"}\n')

        result = query(
            base_dir=base_dir,
            scope="repo",
            type_="rejection",
        )
        assert result == 0
        captured = capsys.readouterr()
        assert "[]" in captured.out

    def test_broken_jsonl_line_skipped(self, tmp_path, capsys):
        """Broken JSONL line → skip + warning, continue."""
        base_dir = tmp_path / ".honne"
        asset_dir = base_dir / "assets"
        asset_dir.mkdir(parents=True)

        # Create rejections.jsonl with one broken line
        rejections_file = asset_dir / "rejections.jsonl"
        rejections_file.write_text(
            '{"id":"r1","type":"rejection"}\n'
            'invalid json line\n'
            '{"id":"r2","type":"rejection"}\n'
        )

        result = query(
            base_dir=base_dir,
            scope="repo",
            type_="rejection",
        )
        assert result == 0
        captured = capsys.readouterr()
        # Should parse valid lines, skip broken line
        output = json.loads(captured.out)
        assert len(output) == 2

    def test_existing_rejections_filtered(self, tmp_path, capsys):
        """Existing rejections with scope filter."""
        base_dir = tmp_path / ".honne"
        asset_dir = base_dir / "assets"
        asset_dir.mkdir(parents=True)

        rejections_file = asset_dir / "rejections.jsonl"
        rejections_file.write_text(
            '{"id":"r1","type":"rejection","scope":"repo","created_at":"2025-01-01T00:00:00Z"}\n'
            '{"id":"r2","type":"rejection","scope":"global","created_at":"2025-01-02T00:00:00Z"}\n'
        )

        # Query for repo scope
        result = query(
            base_dir=base_dir,
            scope="repo",
            type_="rejection",
        )
        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        # Both records returned (scope filter not applied in basic query)
        assert len(output) == 2

    def test_query_type_claim_uses_claims_file(self, tmp_path, capsys):
        """type=claim → read from claims.jsonl."""
        base_dir = tmp_path / ".honne"
        asset_dir = base_dir / "assets"
        asset_dir.mkdir(parents=True)

        # Create claims.jsonl only
        claims_file = asset_dir / "claims.jsonl"
        claims_file.write_text('{"id":"c1","type":"claim"}\n')

        result = query(
            base_dir=base_dir,
            type_="claim",
        )
        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert len(output) == 1

    def test_query_type_evolution_uses_evolutions_file(self, tmp_path, capsys):
        """type=evolution → read from evolutions.jsonl."""
        base_dir = tmp_path / ".honne"
        asset_dir = base_dir / "assets"
        asset_dir.mkdir(parents=True)

        evolutions_file = asset_dir / "evolutions.jsonl"
        evolutions_file.write_text('{"id":"e1","type":"evolution"}\n')

        result = query(
            base_dir=base_dir,
            type_="evolution",
        )
        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert len(output) == 1

    def test_default_base_dir_is_dot_honne(self, tmp_path, monkeypatch, capsys):
        """Default base_dir is .honne in cwd."""
        # Change to temp dir
        monkeypatch.chdir(tmp_path)

        # Create .honne/assets/claims.jsonl
        asset_dir = tmp_path / ".honne" / "assets"
        asset_dir.mkdir(parents=True)
        (asset_dir / "claims.jsonl").write_text('{"id":"c1"}\n')

        # Call with base_dir=None
        result = query(
            base_dir=None,
            type_="claim",
        )
        assert result == 0
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert len(output) == 1
