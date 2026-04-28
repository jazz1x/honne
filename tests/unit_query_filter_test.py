import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from honne_py.query import query


def _write_claims(asset_dir: Path, records: list) -> Path:
    f = asset_dir / "claims.jsonl"
    f.write_text("".join(json.dumps(r) + "\n" for r in records))
    return f


@pytest.fixture
def mixed_claims(tmp_path):
    base_dir = tmp_path / ".honne"
    asset_dir = base_dir / "assets"
    asset_dir.mkdir(parents=True)
    records = [
        {"id": "c1", "axis": "lexicon", "scope": "repo", "created_at": "2025-01-01T00:00:00Z"},
        {"id": "c2", "axis": "reaction", "scope": "repo", "created_at": "2025-01-02T00:00:00Z"},
        {"id": "c3", "axis": "lexicon", "scope": "project", "created_at": "2025-01-03T00:00:00Z"},
        {"id": "c4", "axis": "workflow", "scope": "repo", "created_at": "2025-01-04T00:00:00Z"},
    ]
    _write_claims(asset_dir, records)
    return base_dir


class TestScopeFilter:
    def test_scope_repo_filters_correctly(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, scope="repo", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 3
        assert all(r["scope"] == "repo" for r in out)

    def test_scope_project_filters_correctly(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, scope="project", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 1
        assert out[0]["id"] == "c3"

    def test_scope_none_returns_all(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, scope=None, type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 4

    def test_scope_unknown_returns_empty(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, scope="nonexistent", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 0


class TestTagFilter:
    def test_tag_lexicon_filters_correctly(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, tag="lexicon", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 2
        assert all(r["axis"] == "lexicon" for r in out)

    def test_tag_none_returns_all(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, tag=None, type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 4

    def test_tag_unknown_returns_empty(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, tag="antipattern", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 0


class TestTagsFilter:
    def test_tags_multiple_axes(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, tags="lexicon,reaction", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 3
        assert all(r["axis"] in ("lexicon", "reaction") for r in out)

    def test_tags_single_entry(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, tags="workflow", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 1
        assert out[0]["id"] == "c4"

    def test_tags_with_spaces_stripped(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, tags="lexicon , workflow", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 3


class TestCombinedFilters:
    def test_scope_and_tag_combined(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, scope="repo", tag="lexicon", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 1
        assert out[0]["id"] == "c1"

    def test_scope_and_tag_no_match(self, mixed_claims, capsys):
        query(base_dir=mixed_claims, scope="project", tag="reaction", type_="claim")
        out = json.loads(capsys.readouterr().out)
        assert len(out) == 0
