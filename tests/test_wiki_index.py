"""Tests for index/recent.md, log.md, peer-review.md auto-update."""

from pathlib import Path

import pytest

from main import cmd_init
from scripts.generate import (
    _update_log,
    _update_peer_review,
    _update_recent,
    generate_wiki,
)

SAMPLE_PAPER = {
    "arxiv_id": "2501.00001v1",
    "slug": "test-paper-on-transformers",
    "title": "Test Paper on Transformers",
    "authors": ["Alice Smith", "Bob Jones"],
    "abstract": "This is a test abstract about transformers and attention mechanisms.",
    "url": "https://arxiv.org/abs/2501.00001v1",
    "pdf_url": "https://arxiv.org/pdf/2501.00001v1",
    "published": "2025-01-01",
    "arxiv_categories": ["cs.CL", "cs.LG"],
    "wiki_category": "Post_Training",
    "matched_keyword": "transformer attention",
}

SAMPLE_PAPER_2 = {
    "arxiv_id": "2501.00002v1",
    "slug": "another-paper-on-vision",
    "title": "Another Paper on Vision",
    "authors": ["Carol White"],
    "abstract": "Vision abstract.",
    "url": "https://arxiv.org/abs/2501.00002v1",
    "pdf_url": "https://arxiv.org/pdf/2501.00002v1",
    "published": "2025-01-02",
    "arxiv_categories": ["cs.CV"],
    "wiki_category": "Multimodal",
    "matched_keyword": "vision transformer",
}


@pytest.fixture()
def wiki_root(tmp_path: Path) -> Path:
    root = tmp_path / "wiki"
    root.mkdir()
    return root


class TestUpdateRecent:
    def test_creates_date_section(self, wiki_root: Path) -> None:
        index_dir = wiki_root / "index"
        index_dir.mkdir(parents=True)
        recent = index_dir / "recent.md"
        recent.write_text("# Recently Added\n")

        _update_recent(wiki_root, SAMPLE_PAPER, "2025-01-15")

        content = recent.read_text()
        assert "## 2025-01-15" in content
        assert "test-paper-on-transformers.md" in content
        assert "`2501.00001v1`" in content

    def test_appends_to_existing_date(self, wiki_root: Path) -> None:
        index_dir = wiki_root / "index"
        index_dir.mkdir(parents=True)
        recent = index_dir / "recent.md"
        recent.write_text("# Recently Added\n")

        _update_recent(wiki_root, SAMPLE_PAPER, "2025-01-15")
        _update_recent(wiki_root, SAMPLE_PAPER_2, "2025-01-15")

        content = recent.read_text()
        # Only one date header
        assert content.count("## 2025-01-15") == 1
        assert "test-paper-on-transformers.md" in content
        assert "another-paper-on-vision.md" in content

    def test_skips_if_no_recent_md(self, wiki_root: Path) -> None:
        # Should not raise even if index/recent.md does not exist
        _update_recent(wiki_root, SAMPLE_PAPER, "2025-01-15")


class TestUpdateLog:
    def test_appends_to_log(self, wiki_root: Path) -> None:
        log = wiki_root / "log.md"
        log.write_text(
            "# Change Log\n"
            "\n"
            "All changes are recorded here in reverse chronological order.\n"
        )

        _update_log(wiki_root, [SAMPLE_PAPER], "2025-01-15")

        content = log.read_text()
        assert "## 2025-01-15" in content
        assert "**Added**: Test Paper on Transformers" in content
        assert "`2501.00001v1`" in content
        assert "sources/Post_Training/test-paper-on-transformers.md" in content
        assert "evidence/Post_Training/test-paper-on-transformers.md" in content
        assert "wiki/papers/Post_Training/test-paper-on-transformers.md" in content

    def test_skips_if_no_log(self, wiki_root: Path) -> None:
        # Should not raise even if log.md does not exist
        _update_log(wiki_root, [SAMPLE_PAPER], "2025-01-15")


class TestUpdatePeerReview:
    def test_appends_to_preprint(self, wiki_root: Path) -> None:
        index_dir = wiki_root / "index"
        index_dir.mkdir(parents=True)
        pr = index_dir / "peer-review.md"
        pr.write_text(
            "# Peer-Review Status\n"
            "\n"
            "## accepted\n"
            "\n"
            "| Paper | Venue | Year |\n"
            "|-------|-------|------|\n"
            "\n"
            "## workshop\n"
            "\n"
            "| Paper | Venue | Year |\n"
            "|-------|-------|------|\n"
            "\n"
            "## under-review\n"
            "\n"
            "| Paper | Venue | Year |\n"
            "|-------|-------|------|\n"
            "\n"
            "## preprint\n"
            "\n"
            "| Paper | arXiv ID |\n"
            "|-------|----------|\n"
        )

        _update_peer_review(wiki_root, SAMPLE_PAPER)

        content = pr.read_text()
        assert "| [Test Paper on Transformers]" in content
        assert "| 2501.00001v1 |" in content

    def test_skips_if_no_peer_review(self, wiki_root: Path) -> None:
        # Should not raise even if index/peer-review.md does not exist
        _update_peer_review(wiki_root, SAMPLE_PAPER)


class TestInitExtended:
    @pytest.fixture(autouse=True)
    def isolated(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(tmp_path)

    def test_creates_index_dir(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        assert (tmp_path / "wiki" / "index").is_dir()

    def test_creates_recent_md(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        assert (tmp_path / "wiki" / "index" / "recent.md").exists()

    def test_creates_log_md(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        assert (tmp_path / "wiki" / "log.md").exists()

    def test_creates_schema_md(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        assert (tmp_path / "wiki" / "SCHEMA.md").exists()

    def test_creates_decisions_dir(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        assert (tmp_path / "wiki" / "decisions").is_dir()

    def test_creates_figures_dir(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        assert (tmp_path / "wiki" / "figures").is_dir()


class TestFiguresDir:
    def test_generate_creates_figures_slug_dir(self, wiki_root: Path) -> None:
        generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01")
        figures_dir = wiki_root / "figures" / "Post_Training" / "test-paper-on-transformers"
        assert figures_dir.is_dir()
