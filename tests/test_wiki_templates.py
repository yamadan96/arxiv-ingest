"""Tests for wiki/papers template fields (peer_review, venue, evidence link)."""

from pathlib import Path

import pytest

from scripts.generate import generate_wiki

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


@pytest.fixture()
def wiki_root(tmp_path: Path) -> Path:
    root = tmp_path / "wiki"
    root.mkdir()
    return root


class TestWikiPaperTemplate:
    def test_has_peer_review_field(self, wiki_root: Path) -> None:
        path, _ = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01")
        content = path.read_text()
        assert "peer_review: preprint" in content

    def test_has_venue_field(self, wiki_root: Path) -> None:
        path, _ = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01")
        content = path.read_text()
        assert 'venue: ""' in content

    def test_has_evidence_link(self, wiki_root: Path) -> None:
        path, _ = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01")
        content = path.read_text()
        assert "evidence/Post_Training/test-paper-on-transformers.md" in content

    def test_obsidian_has_peer_review(self, wiki_root: Path) -> None:
        path, _ = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01", obsidian=True)
        content = path.read_text()
        assert "peer_review: preprint" in content
        assert 'venue: ""' in content
        assert "evidence/Post_Training/test-paper-on-transformers.md" in content
