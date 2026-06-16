"""Tests for arxiv-ingest open command."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from main import cmd_open

PAPERS = [
    {
        "arxiv_id": "2501.00001v1",
        "slug": "attention-is-all-you-need",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani, Ashish"],
        "abstract": "Abstract.",
        "url": "https://arxiv.org/abs/2501.00001v1",
        "pdf_url": "https://arxiv.org/pdf/2501.00001v1",
        "published": "2025-01-15",
        "arxiv_categories": ["cs.CL"],
        "wiki_category": "Post_Training",
        "matched_keyword": "transformer",
    }
]


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "fetched.json").write_text(json.dumps(PAPERS))


class TestCmdOpen:
    def test_opens_by_full_arxiv_id(self) -> None:
        with patch("webbrowser.open") as mock_open:
            cmd_open(["2501.00001v1"])
            mock_open.assert_called_once_with("https://arxiv.org/abs/2501.00001v1")

    def test_opens_by_id_without_version(self) -> None:
        with patch("webbrowser.open") as mock_open:
            cmd_open(["2501.00001"])
            mock_open.assert_called_once()

    def test_opens_by_slug(self) -> None:
        with patch("webbrowser.open") as mock_open:
            cmd_open(["attention-is-all-you-need"])
            mock_open.assert_called_once_with("https://arxiv.org/abs/2501.00001v1")

    def test_unknown_id_exits(self) -> None:
        with patch("webbrowser.open"):
            with pytest.raises(SystemExit):
                cmd_open(["nonexistent-id"])

    def test_no_args_exits(self) -> None:
        with pytest.raises(SystemExit):
            cmd_open([])

    def test_missing_fetched_json_exits(self, tmp_path: Path) -> None:
        (tmp_path / "data" / "fetched.json").unlink()
        with pytest.raises(SystemExit):
            cmd_open(["2501.00001v1"])
