# arxiv-ingest

[![Tests](https://github.com/yamadan96/arxiv-ingest/actions/workflows/tests.yml/badge.svg)](https://github.com/yamadan96/arxiv-ingest/actions/workflows/tests.yml)
[![PyPI version](https://img.shields.io/pypi/v/arxiv-ingest)](https://pypi.org/project/arxiv-ingest/)
[![Python 3.11+](https://img.shields.io/pypi/pyversions/arxiv-ingest)](https://pypi.org/project/arxiv-ingest/)

> 日本語 README: [README.ja.md](README.ja.md)

**Fetch recent arXiv papers by keyword and scaffold them into structured research notes.**

Works standalone as a CLI, integrates with Claude Code for LLM-assisted evidence extraction, and auto-runs via GitHub Actions.

## Features

- **Keyword-based collection** — list topics in `config.yaml`, no code needed
- **3-layer wiki** — `sources/` (metadata) · `evidence/` (claims) · `wiki/` (synthesis)
- **Safe re-runs** — already-filled files are never overwritten
- **LLM auto-summary** — `--summarize` fills files via Claude API
- **Date filtering** — `--since=YYYY-MM-DD` for targeted backfills
- **Inspection tools** — `list`, `status`, `search` for managing your corpus
- **Export** — GitHub Issues, BibTeX, CSV
- **Webhook notifications** — post new-paper summaries to Slack or Discord
- **Obsidian integration** — `[[wikilinks]]` and graph view connectivity
- **Quartz integration** — publish directly to a [Quartz v4](https://quartz.jzhao.xyz/) static site
- **Auto-index** — `index/recent.md`, `log.md`, `index/peer-review.md` updated on every run
- **GitHub Actions template** — auto-runs Mon–Fri, `workflow_dispatch` for on-demand runs

## Quick start

```bash
pip install arxiv-ingest

# Initialize wiki directory and config
arxiv-ingest init              # creates config.yaml + research-wiki/

# Edit keywords in config.yaml, then:
arxiv-ingest run               # fetch + generate in one step
```

From source:

```bash
git clone https://github.com/yamadan96/arxiv-ingest
cd arxiv-ingest
uv sync
arxiv-ingest init
```

## Configuration (`config.yaml`)

```yaml
output_dir: "../research-wiki"   # path to your wiki directory
max_results: 20                  # papers per keyword
days_back: 7                     # look back N days

keywords:
  - "Vision-Language Model transformer"
  - "LoRA PEFT fine-tuning language model"
  - "LLM reasoning chain-of-thought"

# Only accept papers in these arXiv categories:
allowed_arxiv_categories: [cs.CV, cs.CL, cs.LG, cs.AI, cs.RO, stat.ML]

# Primary category must be in this list (prevents off-topic papers):
require_primary_in: [cs.CV, cs.CL, cs.AI, cs.RO, stat.ML]

# arXiv category → wiki folder name:
category_map:
  cs.CV: "Multimodal"
  cs.CL: "Post_Training"
  cs.AI: "Reasoning"
  cs.RO: "Physical_AI"
  stat.ML: "Pretraining"

# Optional: post new-paper summaries to Slack or Discord
# webhook_url: "https://hooks.slack.com/services/..."
```

See `config.yaml.example` for all options with documentation.

## Commands reference

| Command | Description |
|---------|-------------|
| `init [wiki-dir]` | Create `config.yaml` and wiki directory skeleton |
| `fetch` | Fetch papers from arXiv → `data/fetched.json` |
| `generate` | Create skeleton files from `fetched.json` |
| `run` | `fetch` + `generate` in one step |
| `list` | List papers in `fetched.json` |
| `status` | Show fill progress (filled / unfilled per layer) |
| `search <term>` | Full-text search across all local wiki files |
| `embed` | Encode paper embeddings for semantic search (requires `[semantic]`) |
| `export` | Export papers to GitHub Issues, BibTeX, or CSV |
| `open <id\|slug>` | Open a paper's arXiv page in the browser |
| `version` | Print the installed version |

### Common flags

```bash
arxiv-ingest fetch --since=2025-01-01   # fetch from a specific date
arxiv-ingest fetch --dry-run            # preview without writing

arxiv-ingest generate --obsidian        # use [[wikilinks]] (Obsidian mode)
arxiv-ingest generate --quartz          # output Quartz-compatible files
arxiv-ingest generate --summarize       # auto-fill via Claude API
arxiv-ingest generate --dry-run         # preview without writing
arxiv-ingest generate --limit=5         # generate for at most 5 papers

arxiv-ingest list --category=Multimodal # filter by wiki category
arxiv-ingest list --unfilled            # only papers with empty wiki pages
arxiv-ingest list --limit=10            # show at most 10 papers
arxiv-ingest list --json                # JSON output for piping to jq

arxiv-ingest search attention --json    # search results as JSON

arxiv-ingest embed                          # encode embeddings for semantic search
arxiv-ingest search --semantic "vision transformer"  # semantic similarity search
arxiv-ingest search --semantic "LoRA" --limit=5      # top 5 semantic results

arxiv-ingest export --format=bibtex          # BibTeX output (no gh needed)
arxiv-ingest export --format=bibtex --limit=5 # top 5 papers as BibTeX
arxiv-ingest export --format=csv             # CSV output
arxiv-ingest export --repo=owner/repo         # GitHub Issues: target repository
arxiv-ingest export --dry-run                 # GitHub Issues: preview only

arxiv-ingest open 2501.00001v1          # open by arXiv ID
arxiv-ingest open attention-is-all      # open by wiki slug
```

## Output format (default)

```
output_dir/
├── SCHEMA.md                         # Wiki conventions
├── log.md                            # Append-only change log (auto-updated)
├── sources/{Category}/{slug}.md      # Metadata — written once, never overwritten
├── evidence/{Category}/{slug}.md     # Claims & benchmarks — fill this in
├── wiki/
│   ├── index.md                      # Manual topic catalog
│   └── papers/{Category}/{slug}.md   # Synthesis & interpretation
├── figures/{Category}/{slug}/        # Paper figures (manual placement)
├── decisions/                        # Adoption / rejection notes
├── presentations/                    # Study session slides
└── index/
    ├── recent.md                     # Auto-updated on every run
    ├── peer-review.md                # Auto-updated on every run
    ├── topics.md                     # Topic index (manual)
    ├── models.md                     # Model index (manual)
    └── open-questions.md             # Open questions (manual)
```

`evidence/` and `wiki/` files are only re-created if they still contain the unfilled template placeholder, so manual edits are safe across re-runs.

## Obsidian integration

[Obsidian](https://obsidian.md/) users can open the wiki directory as a vault and get automatic graph-view connectivity between papers.

```bash
# First-time setup: creates .obsidian/app.json with wikilinks enabled
arxiv-ingest init --obsidian my-research-wiki

# Daily use: generates [[wikilinks]] instead of plain Markdown links
arxiv-ingest run --obsidian
```

What `--obsidian` changes:
- `wiki/papers/` pages use `[[slug]]` instead of `[source](path/to/file.md)`
- `evidence/` pages include a `> Source paper: [[slug]]` backlink

## Quartz integration

[Quartz v4](https://quartz.jzhao.xyz/) users can publish papers directly to a static site with graph view, backlinks, and tag pages.

```bash
# First-time setup: creates content/papers/ and content/templates/
arxiv-ingest init --quartz my-quartz-site

# Daily use: generates content/papers/{YYYY}/{slug}.md
arxiv-ingest run --quartz

# With LLM auto-fill (fills all sections in Japanese)
arxiv-ingest run --quartz --summarize
```

Generated file (`content/papers/2025/attention-is-all-you-need.md`):

```yaml
---
title: "Attention Is All You Need"
authors: "Vaswani, Ashish, Shazeer, Noam, ..."
venue: "arXiv:2501.00001"        # "ICLR 2022 / arXiv:..." when journal_ref available
year: 2025
url: "https://arxiv.org/abs/2501.00001"
code: ""
read_date: 2026-06-16
status: reading
tags:
  - Post_Training
  - transformer
---
```

Sections: TL;DR · 背景・問題設定 · 手法 · 実験 · 強み · 弱み・未解決の問い · 関連研究とのつながり · 自分の研究・実装への示唆

## LLM auto-summary

Install the optional `anthropic` dependency and set your API key:

```bash
pip install 'arxiv-ingest[summarize]'
export ANTHROPIC_API_KEY=sk-ant-...

arxiv-ingest generate --summarize          # fills evidence/ (default mode)
arxiv-ingest generate --quartz --summarize # fills Quartz sections in Japanese
```

Claude reads each paper's abstract and pre-fills the files. Already-edited files are never overwritten.

## Webhook notifications

Add `webhook_url` to `config.yaml` to receive a post-run summary in Slack or Discord:

```yaml
webhook_url: "https://hooks.slack.com/services/T.../B.../..."
# Discord:
# webhook_url: "https://discord.com/api/webhooks/..."
```

The webhook is non-fatal — if it fails, the run continues normally.

## Using with Claude Code

Copy the command file so `/arxiv-ingest` is available as a slash command:

```bash
cp .claude/commands/arxiv-ingest.md ~/.claude/commands/
```

After `arxiv-ingest run`, invoke `/arxiv-ingest` in Claude Code. Claude reads each paper's abstract (and PDF when available) and fills `evidence/` and `wiki/` files automatically.

## GitHub Actions: daily auto-ingest

### Setup

1. Fork or use this repo as a template
2. Create a GitHub Fine-grained PAT with **Write** access to your wiki repo
3. Add to **Settings → Secrets and variables → Actions**:

   | Kind | Name | Value |
   |------|------|-------|
   | Secret | `GH_PAT` | your PAT (needs Write access to wiki/paper-survey repos) |
   | Variable | `WIKI_REPO` | `your-name/research-wiki` (3-layer wiki mode) |
   | Variable | `PAPER_SURVEY_REPO` | `your-name/paper-survey` (Quartz mode, optional) |

4. Go to **Actions → Daily arXiv Ingest → Run workflow** to verify

### Schedule

- **Auto**: Mon–Fri UTC 01:00 — `cron: '0 1 * * 1-5'`
- **Manual**: `workflow_dispatch` with `days_back`, `summarize`, and `quartz` inputs

### Quartz auto-deploy

Enable `quartz: true` in `workflow_dispatch` to push directly to your Quartz site:

```
Actions → Daily arXiv Ingest → Run workflow → quartz: ✓
```

Commits go to `PAPER_SURVEY_REPO` under `content/papers/{YYYY}/{slug}.md`.
Quartz's own deploy workflow picks up the push and rebuilds the site automatically.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## License

MIT
