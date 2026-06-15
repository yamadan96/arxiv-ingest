"""Tests for scripts/fetch.py"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from scripts.fetch import load_config, map_category, slugify


class TestSlugify:
    def test_lowercases(self) -> None:
        assert slugify("Hello World") == "hello-world"

    def test_strips_special_chars(self) -> None:
        assert slugify("ViT: Vision Transformer!") == "vit-vision-transformer"

    def test_collapses_spaces(self) -> None:
        assert slugify("a  b   c") == "a-b-c"

    def test_truncates_to_80(self) -> None:
        long_title = "word " * 30
        assert len(slugify(long_title)) <= 80

    def test_no_leading_trailing_dash(self) -> None:
        result = slugify("  spaces  ")
        assert not result.startswith("-")
        assert not result.endswith("-")

    def test_empty_string(self) -> None:
        assert slugify("") == ""


class TestMapCategory:
    CATEGORY_MAP = {
        "cs.CV": "Multimodal",
        "cs.CL": "Post_Training",
        "cs.AI": "Reasoning",
        "cs.RO": "Physical_AI",
        "stat.ML": "Pretraining",
    }

    def test_primary_maps_correctly(self) -> None:
        assert map_category(["cs.CV", "cs.LG"], self.CATEGORY_MAP) == "Multimodal"

    def test_secondary_used_when_primary_missing(self) -> None:
        assert map_category(["cs.LG", "cs.CL"], self.CATEGORY_MAP) == "Post_Training"

    def test_unknown_returns_default(self) -> None:
        assert map_category(["cs.DS"], self.CATEGORY_MAP) == "Architecture"

    def test_empty_list_returns_default(self) -> None:
        assert map_category([], self.CATEGORY_MAP) == "Architecture"

    def test_stat_ml(self) -> None:
        assert map_category(["stat.ML"], self.CATEGORY_MAP) == "Pretraining"


class TestLoadConfig:
    def test_loads_yaml(self, tmp_path: Path) -> None:
        config = {"keywords": ["transformer"], "days_back": 3}
        f = tmp_path / "config.yaml"
        f.write_text(yaml.dump(config))
        result = load_config(f)
        assert result["keywords"] == ["transformer"]
        assert result["days_back"] == 3

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")
