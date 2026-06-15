# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-06-15

### Added
- `arxiv-ingest export` — export fetched papers to GitHub Issues via `gh` CLI
  - Automatic label mapping from wiki categories (cv / nlp / ai / robotics / ml)
  - Issue body includes abstract, authors, arXiv URL, and a read checklist
  - `--repo=owner/repo` flag to target a specific repository
  - `--dry-run` flag to preview without creating issues

## [0.6.0] - 2026-06-15

### Added
- `arxiv-ingest search <term>` — full-text search across all local wiki files
  - Scans sources, evidence, and wiki layers
  - Highlights matched keyword in the snippet column

## [0.5.0] - 2026-06-15

### Added
- `arxiv-ingest status` — show fill progress (filled / unfilled counts per layer)
  - Distinguishes unfilled template files from manually edited ones

## [0.4.0] - 2026-06-15

### Added
- `--dry-run` flag for `fetch`, `generate`, and `run`
  - `fetch --dry-run`: prints results table without saving `data/fetched.json`
  - `generate --dry-run`: reports would-create / skip without writing files

### Fixed
- `fetch` error message now suggests `arxiv-ingest init` instead of `cp config.yaml.example`

## [0.3.0] - 2026-06-15

### Added
- `arxiv-ingest init [wiki-dir]` — one-command setup for new users
  - Creates `config.yaml` from bundled example (skips if already present)
  - Patches `output_dir` to match the chosen wiki directory
  - Scaffolds `sources/`, `evidence/`, and `wiki/papers/` with default category subdirectories
  - Creates `data/` directory for `fetched.json`
  - Idempotent: safe to run multiple times

## [0.2.0] - 2026-06-15

### Added
- Proper CLI entry point via `[project.scripts]` — `arxiv-ingest fetch|generate|run|--help`
- English templates replacing Japanese placeholders
- Language-neutral dedup sentinel `<!-- arxiv-ingest: unfilled -->` in evidence/wiki files
- Error handling in `fetch`: missing `config.yaml`, empty keywords, arXiv API errors
- Test suite (42 tests across `test_fetch`, `test_generate`, `test_init`)
- CI workflow running pytest on Python 3.11, 3.12, 3.13
- PyPI publication — `pip install arxiv-ingest`

## [0.1.0] - 2026-04-24

### Added
- Initial release
- `scripts/fetch.py` — keyword-based arXiv paper collection with category filtering
- `scripts/generate.py` — 3-layer skeleton generation (sources / evidence / wiki)
- `config.yaml.example` with full option documentation
- GitHub Actions daily workflow (Mon–Fri UTC 01:00)
- Claude Code slash command integration (`/arxiv-ingest`)
