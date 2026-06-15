"""Tests for arxiv-ingest list command."""

import json
from pathlib import Path

import pytest

from main import cmd_list

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


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "fetched.json").write_text(json.dumps(PAPERS))


class TestCmdList:
    def test_no_args_does_not_raise(self) -> None:
        cmd_list([])  # should print table and return

    def test_category_filter(self, capsys: pytest.CaptureFixture) -> None:
        cmd_list(["--category=Multimodal"])
        # only paper-two should appear
        out = capsys.readouterr().out
        assert "Paper Two" in out
        assert "Paper One" not in out

    def test_category_filter_case_insensitive(self, capsys: pytest.CaptureFixture) -> None:
        cmd_list(["--category=multimodal"])
        out = capsys.readouterr().out
        assert "Paper Two" in out

    def test_missing_fetched_json_exits(self, tmp_path: Path) -> None:
        (tmp_path / "data" / "fetched.json").unlink()
        with pytest.raises(SystemExit):
            cmd_list([])
