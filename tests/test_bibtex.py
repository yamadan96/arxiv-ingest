"""Tests for BibTeX and CSV export (arxiv-ingest export --format=bibtex/csv)."""

import csv
import io
import json
from pathlib import Path

import pytest

from main import _bibtex_key, _to_bibtex, _to_csv, cmd_export

PAPER = {
    "arxiv_id": "2501.00001v1",
    "slug": "attention-is-all-you-need",
    "title": "Attention Is All You Need",
    "authors": ["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki"],
    "abstract": "The dominant sequence transduction models...",
    "url": "https://arxiv.org/abs/2501.00001v1",
    "pdf_url": "https://arxiv.org/pdf/2501.00001v1",
    "published": "2025-01-15",
    "arxiv_categories": ["cs.CL", "cs.LG"],
    "wiki_category": "Post_Training",
    "matched_keyword": "transformer",
}


@pytest.fixture()
def with_fetched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "fetched.json").write_text(json.dumps([PAPER]))
    return tmp_path


class TestBibtexKey:
    def test_key_format(self) -> None:
        key = _bibtex_key(PAPER)
        assert key == "vaswani2025attention"

    def test_key_uses_last_name(self) -> None:
        p = {**PAPER, "authors": ["John Smith"]}
        assert _bibtex_key(p).startswith("smith")

    def test_key_fallback_no_authors(self) -> None:
        p = {**PAPER, "authors": []}
        key = _bibtex_key(p)
        assert "unknown" in key

    def test_key_fallback_no_alpha_title(self) -> None:
        p = {**PAPER, "title": "123 456"}
        key = _bibtex_key(p)
        assert "paper" in key


class TestToBibtex:
    def test_is_misc_entry(self) -> None:
        bib = _to_bibtex(PAPER)
        assert bib.startswith("@misc{")

    def test_contains_title(self) -> None:
        bib = _to_bibtex(PAPER)
        assert "Attention Is All You Need" in bib

    def test_strips_version_from_eprint(self) -> None:
        bib = _to_bibtex(PAPER)
        assert "eprint" in bib
        assert "2501.00001}" in bib
        assert "v1" not in bib.split("eprint")[1].split("\n")[0]

    def test_primary_class_is_first_category(self) -> None:
        bib = _to_bibtex(PAPER)
        assert "cs.CL" in bib

    def test_url_present(self) -> None:
        bib = _to_bibtex(PAPER)
        assert "arxiv.org/abs/2501.00001v1" in bib

    def test_author_and_separators(self) -> None:
        bib = _to_bibtex(PAPER)
        assert "Vaswani, Ashish and Shazeer, Noam" in bib


class TestCmdExportBibtex:
    def test_outputs_bibtex(
        self, with_fetched: Path, capsys: pytest.CaptureFixture
    ) -> None:
        cmd_export(["--format=bibtex"])
        out = capsys.readouterr().out
        assert "@misc{" in out
        assert "Attention Is All You Need" in out

    def test_no_gh_required(
        self, with_fetched: Path, capsys: pytest.CaptureFixture
    ) -> None:
        # Should not raise even without gh installed
        cmd_export(["--format=bibtex"])
        out = capsys.readouterr().out
        assert out.strip()

    def test_multiple_papers_separated(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
    ) -> None:
        monkeypatch.chdir(tmp_path)
        (tmp_path / "data").mkdir()
        papers = [PAPER, {**PAPER, "arxiv_id": "2501.00002v1", "title": "Another Paper", "authors": ["Lee, Bob"]}]
        (tmp_path / "data" / "fetched.json").write_text(json.dumps(papers))
        cmd_export(["--format=bibtex"])
        out = capsys.readouterr().out
        assert out.count("@misc{") == 2


class TestToCSV:
    def test_has_header_row(self) -> None:
        out = _to_csv([PAPER])
        reader = csv.DictReader(io.StringIO(out))
        assert reader.fieldnames is not None
        assert "title" in reader.fieldnames
        assert "arxiv_id" in reader.fieldnames

    def test_contains_paper_data(self) -> None:
        out = _to_csv([PAPER])
        reader = csv.DictReader(io.StringIO(out))
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["title"] == "Attention Is All You Need"
        assert rows[0]["arxiv_id"] == "2501.00001v1"
        assert rows[0]["published"] == "2025-01-15"

    def test_authors_semicolon_separated(self) -> None:
        out = _to_csv([PAPER])
        reader = csv.DictReader(io.StringIO(out))
        rows = list(reader)
        assert "Vaswani, Ashish" in rows[0]["authors"]


class TestCmdExportCSV:
    def test_outputs_csv(
        self, with_fetched: Path, capsys: pytest.CaptureFixture
    ) -> None:
        cmd_export(["--format=csv"])
        out = capsys.readouterr().out
        assert "title" in out.splitlines()[0]
        assert "Attention Is All You Need" in out

    def test_no_gh_required_for_csv(
        self, with_fetched: Path, capsys: pytest.CaptureFixture
    ) -> None:
        cmd_export(["--format=csv"])
        out = capsys.readouterr().out
        assert out.strip()
