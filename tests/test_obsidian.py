"""Tests for Obsidian integration (--obsidian flag)."""

import json
from pathlib import Path

import pytest

from main import cmd_init
from scripts.generate import generate_evidence, generate_wiki

PAPER = {
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


@pytest.fixture()
def wiki(tmp_path: Path) -> Path:
    root = tmp_path / "wiki"
    root.mkdir()
    return root


class TestInitObsidian:
    def test_creates_obsidian_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        cmd_init(["--obsidian", "my-wiki"])
        assert (tmp_path / "my-wiki" / ".obsidian").is_dir()

    def test_creates_app_json(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        cmd_init(["--obsidian", "my-wiki"])
        app_json = tmp_path / "my-wiki" / ".obsidian" / "app.json"
        assert app_json.exists()
        cfg = json.loads(app_json.read_text())
        assert cfg["useMarkdownLinks"] is False

    def test_no_obsidian_flag_skips_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        cmd_init(["my-wiki"])
        assert not (tmp_path / "my-wiki" / ".obsidian").exists()


class TestGenerateWikiObsidian:
    def test_uses_wikilinks(self, wiki: Path) -> None:
        _, created = generate_wiki(PAPER, wiki, "2025-01-15", obsidian=True)
        assert created
        out = wiki / "wiki" / "papers" / "Post_Training" / "attention-is-all-you-need.md"
        content = out.read_text()
        assert "[[attention-is-all-you-need]]" in content

    def test_no_markdown_link(self, wiki: Path) -> None:
        generate_wiki(PAPER, wiki, "2025-01-15", obsidian=True)
        out = wiki / "wiki" / "papers" / "Post_Training" / "attention-is-all-you-need.md"
        content = out.read_text()
        assert "../../../sources/" not in content

    def test_standard_mode_uses_markdown_link(self, wiki: Path) -> None:
        generate_wiki(PAPER, wiki, "2025-01-15", obsidian=False)
        out = wiki / "wiki" / "papers" / "Post_Training" / "attention-is-all-you-need.md"
        content = out.read_text()
        assert "../../../sources/" in content


class TestGenerateEvidenceObsidian:
    def test_has_backlink(self, wiki: Path) -> None:
        _, created = generate_evidence(PAPER, wiki, "2025-01-15", obsidian=True)
        assert created
        out = wiki / "evidence" / "Post_Training" / "attention-is-all-you-need.md"
        content = out.read_text()
        assert "[[attention-is-all-you-need]]" in content

    def test_standard_mode_no_backlink(self, wiki: Path) -> None:
        generate_evidence(PAPER, wiki, "2025-01-15", obsidian=False)
        out = wiki / "evidence" / "Post_Training" / "attention-is-all-you-need.md"
        content = out.read_text()
        assert "[[" not in content
