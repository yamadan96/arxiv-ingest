# Contributing to arxiv-ingest

Thank you for your interest in contributing! This guide covers everything you need to get started.

## Quick start

```bash
git clone https://github.com/yamadan96/arxiv-ingest
cd arxiv-ingest
uv sync --all-extras   # installs dev deps + optional summarize extra
```

## Running tests

```bash
uv run pytest tests/ -v
```

All 42 tests must pass before submitting a PR. CI runs the same suite on Python 3.11, 3.12, and 3.13.

## Project structure

```
arxiv-ingest/
├── main.py               # CLI entry point (init/fetch/generate/run/status/search/export)
├── scripts/
│   ├── fetch.py          # arXiv API search and paper collection
│   ├── generate.py       # 3-layer skeleton file generation + dedup logic
│   └── summarize.py      # LLM-based evidence auto-fill (optional)
├── tests/
│   ├── test_fetch.py     # slugify, map_category, load_config
│   ├── test_generate.py  # is_template, generate_sources/evidence/wiki
│   └── test_init.py      # cmd_init scaffold and idempotency
├── config.yaml.example   # Reference configuration with all options documented
└── .github/workflows/
    ├── daily.yml         # Scheduled arXiv ingest (Mon–Fri UTC 01:00)
    └── tests.yml         # CI: pytest on push / PR
```

## Adding a new command

1. Add `def cmd_<name>(args: list[str]) -> None` to `main.py`
2. Register it in the `commands` dict inside `main()`
3. Add a line to `print_help()`
4. Write tests in `tests/test_<name>.py`

## Adding a new config option

1. Document it in `config.yaml.example` with an inline comment
2. Read it in the relevant script with `config.get("option_name", default)`
3. Update `README.md` configuration table

## Code style

- Python 3.11+ type hints on all functions
- No comments unless the *why* is non-obvious
- `ruff` for linting (`uv run ruff check .`)

## Submitting a PR

1. Fork the repo and create a branch: `git checkout -b feat/my-feature`
2. Make your changes and add tests
3. Ensure `uv run pytest tests/ -v` passes
4. Open a PR against `main` — CI will run automatically

## Reporting bugs

Open an issue at https://github.com/yamadan96/arxiv-ingest/issues with:
- Your `arxiv-ingest --help` output (shows version)
- Your `config.yaml` (redact any private keywords)
- The full error message

## License

By contributing you agree that your contributions will be licensed under the MIT License.
