"""Tests for arxiv-ingest init command."""

import sys
from pathlib import Path

import pytest

from main import cmd_init


@pytest.fixture(autouse=True)
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)


class TestCmdInit:
    def test_creates_config_yaml(self, tmp_path: Path) -> None:
        cmd_init([])
        assert (tmp_path / "config.yaml").exists()

    def test_default_wiki_dir_is_research_wiki(self, tmp_path: Path) -> None:
        cmd_init([])
        assert (tmp_path / "research-wiki").is_dir()

    def test_custom_wiki_dir(self, tmp_path: Path) -> None:
        cmd_init(["my-papers"])
        assert (tmp_path / "my-papers").is_dir()

    def test_output_dir_patched_in_config(self, tmp_path: Path) -> None:
        cmd_init(["my-papers"])
        config_text = (tmp_path / "config.yaml").read_text()
        assert 'output_dir: "my-papers"' in config_text

    def test_wiki_layer_dirs_exist(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        assert (tmp_path / "wiki" / "sources").is_dir()
        assert (tmp_path / "wiki" / "evidence").is_dir()
        assert (tmp_path / "wiki" / "wiki" / "papers").is_dir()

    def test_category_subdirs_exist(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        assert (tmp_path / "wiki" / "sources" / "Multimodal").is_dir()
        assert (tmp_path / "wiki" / "evidence" / "Post_Training").is_dir()
        assert (tmp_path / "wiki" / "wiki" / "papers" / "Reasoning").is_dir()

    def test_data_dir_created(self, tmp_path: Path) -> None:
        cmd_init([])
        assert (tmp_path / "data").is_dir()

    def test_does_not_overwrite_existing_config(self, tmp_path: Path) -> None:
        (tmp_path / "config.yaml").write_text("custom: true\n")
        cmd_init([])
        assert "custom: true" in (tmp_path / "config.yaml").read_text()

    def test_idempotent(self, tmp_path: Path) -> None:
        cmd_init(["wiki"])
        cmd_init(["wiki"])  # second run should not raise
        assert (tmp_path / "wiki" / "sources").is_dir()
