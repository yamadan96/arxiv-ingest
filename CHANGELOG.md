# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.18.0] - 2026-06-16

### Added
- Extended `init` scaffold: `wiki/topics/`, `wiki/models/`, `wiki/comparisons/`, `wiki/benchmarks/`, `wiki/engineering/`, `decisions/`, `figures/`, `index/`, `presentations/` directories
- `init` now creates skeleton index files: `index/recent.md`, `index/topics.md`, `index/models.md`, `index/peer-review.md`, `index/open-questions.md`, `log.md`, `wiki/index.md`, `SCHEMA.md`
- `generate` auto-appends to `index/recent.md` when new papers are added
- `generate` auto-appends to `log.md` after each run
- `generate` auto-appends to `index/peer-review.md` (preprint section) for new papers
- `generate` auto-creates `figures/{Category}/{slug}/` directory for each new paper
- `wiki/papers/` template now includes `peer_review: preprint`, `venue: ""` frontmatter fields, peer-review banner, and evidence link

## [0.17.0] - 2026-06-16

### Added
- `--limit=<N>` flag for `list` and `export` — show or export at most N papers
  - `arxiv-ingest list --limit=5` — preview the most recent 5 papers
  - `arxiv-ingest export --format=bibtex --limit=10 > top10.bib` — export first 10 as BibTeX
  - Applied after all other filters (category, unfilled) and format routing

## [0.16.0] - 2026-06-16

### Added
- Obsidian integration via `--obsidian` flag
  - `arxiv-ingest init --obsidian` — creates `.obsidian/app.json` with wikilinks enabled
  - `arxiv-ingest generate --obsidian` — uses `[[wikilinks]]` in wiki and evidence templates
  - `arxiv-ingest run --obsidian` — fetch + generate with Obsidian templates in one step
  - Evidence files get `> Source paper: [[slug]]` backlink for graph view connectivity

## [0.15.0] - 2026-06-16

### Added
- `export --format=csv` — output all fetched papers as CSV to stdout
  - Columns: title, authors, published, category, arxiv_id, url, matched_keyword
  - `arxiv-ingest export --format=csv > papers.csv`
  - No extra dependencies (stdlib `csv`)

## [0.14.0] - 2026-06-16

### Added
- `arxiv-ingest open <arxiv-id|slug>` — open a paper's arXiv page in the default browser
  - Matches by arXiv ID (with or without version suffix) or wiki slug
  - Uses Python stdlib `webbrowser` — no extra dependencies

## [0.13.0] - 2026-06-16

### Added
- `export --format=bibtex` — output all fetched papers as BibTeX `@misc` entries to stdout
  - `arxiv-ingest export --format=bibtex > papers.bib`
  - No dependencies: works without the `gh` CLI
  - Cite key format: `firstauthorYYYYfirstword` (e.g. `vaswani2017attention`)
- `daily.yml` now supports `summarize: boolean` workflow input — set to `true` to auto-fill evidence via Claude API

### Fixed
- `arxiv-ingest search --json` no longer includes Rich markup (`[bold yellow]...`) in snippet text
- `search --json` output now includes a `path` field with the full relative file path
- `arxiv-ingest run` now correctly passes `--since=` and other flags through to `fetch`

## [0.12.0] - 2026-06-15

### Added
- `arxiv-ingest version` — print the installed version
- `--json` flag for `list` and `search` — machine-readable JSON output for piping to `jq`

## [0.11.0] - 2026-06-15

### Added
- Webhook notification support (Slack / Discord)
  - Set `webhook_url` in `config.yaml` to receive new-paper summaries
  - Auto-detects Slack vs Discord format; no additional dependencies (stdlib `urllib`)
  - Non-fatal: webhook errors are logged but do not abort the run

## [0.10.0] - 2026-06-15

### Added
- `arxiv-ingest list` — list papers in `data/fetched.json`
  - `--category=<name>` filter by wiki category
  - `--unfilled` show only papers with unfilled wiki pages

## [0.9.0] - 2026-06-15

### Added
- `fetch --since=YYYY-MM-DD` — fetch papers from a specific date (overrides `days_back`)
- `run --since=YYYY-MM-DD` — convenience pass-through

### Fixed
- Auto-publish CI (`publish.yml`): runs pytest before publishing; requires `PYPI_TOKEN` secret

## [0.8.0] - 2026-06-15

### Added
- `generate --summarize` — auto-fill evidence files using Claude Haiku
  - Extracts key claims, contributions, limitations, and implementation notes from the abstract
  - Optional extra: `anthropic>=0.40.0` — base install unaffected
  - Requires `ANTHROPIC_API_KEY` environment variable
- `scripts/summarize.py`: prompt design, API call, response parser, evidence writer

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
