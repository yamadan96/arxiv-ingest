"""Tests for arxiv-ingest version command and --json output flags."""

import json
from pathlib import Path

import pytest

from main import cmd_list, cmd_search, cmd_version

PAPERS = [
    {
        "arxiv_id": "2501.00001v1",
        "slug": "paper-one",
        "title": "Paper One on Transformers",
        "authors": ["Alice"],
        "abstract": "Abstract one.",
        "url": "https://arxiv.org/abs/2501.00001v1",
        "pdf_url": "https://arxiv.org/pdf/2501.00001v1",
        "published": "2025-01-01",
        "arxiv_categories": ["cs.CL"],
        "wiki_category": "Post_Training",
        "matched_keyword": "transformer",
    },
    {
        "arxiv_id": "2501.00002v1",
        "slug": "paper-two",
        "title": "Paper Two on Vision",
        "authors": ["Bob"],
        "abstract": "Abstract two.",
        "url": "https://arxiv.org/abs/2501.00002v1",
        "pdf_url": "https://arxiv.org/pdf/2501.00002v1",
        "published": "2025-01-02",
        "arxiv_categories": ["cs.CV"],
        "wiki_category": "Multimodal",
        "matched_keyword": "vision",
    },
]


@pytest.fixture()
def with_fetched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "fetched.json").write_text(json.dumps(PAPERS))
    return tmp_path


class TestCmdVersion:
    def test_prints_version(self, capsys: pytest.CaptureFixture) -> None:
        cmd_version([])
        out = capsys.readouterr().out.strip()
        # Should be a semver-like string, not empty or "unknown"
        assert out
        assert out != "unknown"

    def test_version_format(self, capsys: pytest.CaptureFixture) -> None:
        cmd_version([])
        out = capsys.readouterr().out.strip()
        parts = out.split(".")
        assert len(parts) >= 2
        assert all(p.isdigit() for p in parts[:2])


class TestCmdListJson:
    def test_json_output_is_valid(
        self, with_fetched: Path, capsys: pytest.CaptureFixture
    ) -> None:
        cmd_list(["--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) == 2

    def test_json_output_contains_fields(
        self, with_fetched: Path, capsys: pytest.CaptureFixture
    ) -> None:
        cmd_list(["--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data[0]["arxiv_id"] == "2501.00001v1"
        assert data[0]["title"] == "Paper One on Transformers"

    def test_json_with_category_filter(
        self, with_fetched: Path, capsys: pytest.CaptureFixture
    ) -> None:
        cmd_list(["--json", "--category=Multimodal"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert len(data) == 1
        assert data[0]["wiki_category"] == "Multimodal"


class TestCmdSearchJson:
    def test_json_output_is_valid(
        self, with_fetched: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        # Create a wiki file to search
        wiki = with_fetched / "research-wiki"
        (wiki / "sources" / "Post_Training").mkdir(parents=True)
        (wiki / "sources" / "Post_Training" / "paper-one.md").write_text(
            "# Paper One on Transformers\nAbstract: great transformer paper."
        )
        # Write minimal config
        (with_fetched / "config.yaml").write_text(
            f'output_dir: "{wiki}"\n'
        )
        cmd_search(["transformer", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert isinstance(data, list)
        assert len(data) >= 1
        assert "layer" in data[0]
        assert "file" in data[0]
        assert "path" in data[0]
        assert "snippet" in data[0]
        # snippet must not contain rich markup
        assert "[bold" not in data[0]["snippet"]

    def test_json_empty_result_is_list(
        self, with_fetched: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        wiki = with_fetched / "research-wiki"
        wiki.mkdir()
        (with_fetched / "config.yaml").write_text(f'output_dir: "{wiki}"\n')
        cmd_search(["nonexistent_xyz_term", "--json"])
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data == []
