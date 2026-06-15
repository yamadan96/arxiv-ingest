"""Tests for scripts/generate.py"""

import json
from pathlib import Path

import pytest

from scripts.generate import (
    _TEMPLATE_MARKER,
    generate_evidence,
    generate_sources,
    generate_wiki,
    is_template,
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


@pytest.fixture
def wiki_root(tmp_path: Path) -> Path:
    return tmp_path / "wiki"


class TestIsTemplate:
    def test_missing_file_is_not_template(self, tmp_path: Path) -> None:
        assert not is_template(tmp_path / "nonexistent.md")

    def test_file_with_marker_is_template(self, tmp_path: Path) -> None:
        f = tmp_path / "test.md"
        f.write_text(f"# Title\n{_TEMPLATE_MARKER}\n- (fill in)")
        assert is_template(f)

    def test_filled_file_is_not_template(self, tmp_path: Path) -> None:
        f = tmp_path / "test.md"
        f.write_text("# Title\n\n- This paper proposes a new method.\n")
        assert not is_template(f)


class TestGenerateSources:
    def test_creates_file(self, wiki_root: Path) -> None:
        path, created = generate_sources(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert created
        assert path.exists()

    def test_contains_arxiv_id(self, wiki_root: Path) -> None:
        path, _ = generate_sources(SAMPLE_PAPER, wiki_root, "2025-01-01")
        content = path.read_text()
        assert "2501.00001v1" in content

    def test_contains_title(self, wiki_root: Path) -> None:
        path, _ = generate_sources(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert "Test Paper on Transformers" in path.read_text()

    def test_does_not_overwrite_existing(self, wiki_root: Path) -> None:
        path, _ = generate_sources(SAMPLE_PAPER, wiki_root, "2025-01-01")
        path.write_text("# manually edited")
        _, created = generate_sources(SAMPLE_PAPER, wiki_root, "2025-01-02")
        assert not created
        assert path.read_text() == "# manually edited"

    def test_placed_in_correct_category(self, wiki_root: Path) -> None:
        path, _ = generate_sources(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert path.parent.name == "Post_Training"
        assert path.parent.parent.name == "sources"


class TestGenerateEvidence:
    def test_creates_file_with_marker(self, wiki_root: Path) -> None:
        path, created = generate_evidence(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert created
        assert _TEMPLATE_MARKER in path.read_text()

    def test_does_not_overwrite_filled_file(self, wiki_root: Path) -> None:
        path, _ = generate_evidence(SAMPLE_PAPER, wiki_root, "2025-01-01")
        path.write_text("# filled in evidence without marker")
        _, created = generate_evidence(SAMPLE_PAPER, wiki_root, "2025-01-02")
        assert not created
        assert "filled in evidence" in path.read_text()

    def test_overwrites_unfilled_template(self, wiki_root: Path) -> None:
        path, _ = generate_evidence(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert is_template(path)
        _, created = generate_evidence(SAMPLE_PAPER, wiki_root, "2025-01-02")
        assert created  # still a template → re-created (date updated)

    def test_placed_in_correct_category(self, wiki_root: Path) -> None:
        path, _ = generate_evidence(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert path.parent.name == "Post_Training"
        assert path.parent.parent.name == "evidence"


class TestGenerateWiki:
    def test_creates_file_with_marker(self, wiki_root: Path) -> None:
        path, created = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert created
        assert _TEMPLATE_MARKER in path.read_text()

    def test_does_not_overwrite_filled_file(self, wiki_root: Path) -> None:
        path, _ = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01")
        path.write_text("# filled wiki page without marker")
        _, created = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-02")
        assert not created

    def test_contains_source_link(self, wiki_root: Path) -> None:
        path, _ = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert "sources/Post_Training/test-paper-on-transformers.md" in path.read_text()

    def test_placed_in_correct_path(self, wiki_root: Path) -> None:
        path, _ = generate_wiki(SAMPLE_PAPER, wiki_root, "2025-01-01")
        assert path.parent.name == "Post_Training"
        assert path.parent.parent.name == "papers"
        assert path.parent.parent.parent.name == "wiki"
