"""Tests for Quartz output mode (--quartz flag)."""

from pathlib import Path

import pytest

from main import cmd_init
from scripts.generate import (
    _venue_string,
    generate_quartz,
    is_template,
)

PAPER = {
    "arxiv_id": "2501.00001v1",
    "slug": "attention-is-all-you-need",
    "title": "Attention Is All You Need",
    "authors": ["Vaswani, Ashish", "Shazeer, Noam"],
    "abstract": "Abstract.",
    "url": "https://arxiv.org/abs/2501.00001v1",
    "pdf_url": "https://arxiv.org/pdf/2501.00001v1",
    "published": "2025-01-15",
    "arxiv_categories": ["cs.CL"],
    "wiki_category": "Post_Training",
    "matched_keyword": "transformer",
    "journal_ref": "",
}


@pytest.fixture()
def wiki(tmp_path: Path) -> Path:
    root = tmp_path / "wiki"
    root.mkdir()
    return root


class TestGenerateQuartz:
    def test_creates_in_year_folder(self, wiki: Path) -> None:
        path, created = generate_quartz(PAPER, wiki, "2025-01-15")
        assert created
        assert path.exists()
        assert path == wiki / "content" / "papers" / "2025" / "attention-is-all-you-need.md"

    def test_frontmatter_title(self, wiki: Path) -> None:
        path, _ = generate_quartz(PAPER, wiki, "2025-01-15")
        content = path.read_text()
        assert 'title: "Attention Is All You Need"' in content

    def test_frontmatter_authors_string(self, wiki: Path) -> None:
        path, _ = generate_quartz(PAPER, wiki, "2025-01-15")
        content = path.read_text()
        assert 'authors: "Vaswani, Ashish, Shazeer, Noam"' in content

    def test_frontmatter_venue_arxiv(self, wiki: Path) -> None:
        path, _ = generate_quartz(PAPER, wiki, "2025-01-15")
        content = path.read_text()
        assert 'venue: "arXiv:2501.00001"' in content

    def test_frontmatter_year_integer(self, wiki: Path) -> None:
        path, _ = generate_quartz(PAPER, wiki, "2025-01-15")
        content = path.read_text()
        assert "year: 2025" in content
        # Ensure it is NOT a quoted string
        assert 'year: "2025"' not in content

    def test_frontmatter_status_reading(self, wiki: Path) -> None:
        path, _ = generate_quartz(PAPER, wiki, "2025-01-15")
        content = path.read_text()
        assert "status: reading" in content

    def test_has_sentinel(self, wiki: Path) -> None:
        path, _ = generate_quartz(PAPER, wiki, "2025-01-15")
        content = path.read_text()
        assert "<!-- arxiv-ingest: unfilled -->" in content

    def test_no_overwrite_filled(self, wiki: Path) -> None:
        path, _ = generate_quartz(PAPER, wiki, "2025-01-15")
        # Simulate user filling in the file (remove sentinel)
        path.write_text("# Manually filled content without sentinel")
        _, created = generate_quartz(PAPER, wiki, "2025-01-16")
        assert not created
        assert "Manually filled" in path.read_text()

    def test_sections_present(self, wiki: Path) -> None:
        path, _ = generate_quartz(PAPER, wiki, "2025-01-15")
        content = path.read_text()
        for section in [
            "## TL;DR",
            "## 背景・問題設定",
            "## 手法",
            "## 実験",
            "## 強み",
            "## 弱み・未解決の問い",
            "## 関連研究とのつながり",
            "## 自分の研究・実装への示唆",
        ]:
            assert section in content


class TestInitQuartz:
    def test_creates_content_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        cmd_init(["--quartz", "my-wiki"])
        assert (tmp_path / "my-wiki" / "content" / "papers").is_dir()

    def test_creates_templates_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        cmd_init(["--quartz", "my-wiki"])
        assert (tmp_path / "my-wiki" / "content" / "templates").is_dir()

    def test_creates_index_md(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        cmd_init(["--quartz", "my-wiki"])
        index = tmp_path / "my-wiki" / "content" / "index.md"
        assert index.exists()
        content = index.read_text()
        assert "Paper Survey" in content

    def test_no_quartz_flag_skips_content_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)
        cmd_init(["my-wiki"])
        assert not (tmp_path / "my-wiki" / "content" / "papers").exists()


class TestVenueString:
    def test_with_journal_ref(self) -> None:
        paper = {**PAPER, "journal_ref": "ICLR 2022"}
        result = _venue_string(paper)
        assert result == "ICLR 2022 / arXiv:2501.00001"

    def test_without_journal_ref(self) -> None:
        result = _venue_string(PAPER)
        assert result == "arXiv:2501.00001"
