# arxiv-ingest

**Fetch recent arXiv papers by keyword and scaffold them into structured research notes.**

Works standalone as a CLI, or integrates with Claude Code for LLM-assisted evidence extraction and wiki generation.

## Features

- **Keyword-based collection** — list topics in `config.yaml`, no code needed
- **3-layer output** — `sources/` (metadata) · `evidence/` (claims) · `wiki/` (synthesis)
- **Safe re-runs** — already-filled files are never overwritten
- **GitHub Actions template** — auto-runs Mon–Fri, `workflow_dispatch` for on-demand runs
- **Any wiki** — point `output_dir` at any directory

## Quick start

```bash
# Install (requires Python 3.11+)
pip install arxiv-ingest

# Or from source:
git clone https://github.com/yamadan96/arxiv-ingest
cd arxiv-ingest
uv sync

# Configure
cp config.yaml.example config.yaml
# Edit config.yaml: set keywords, output_dir, and category mappings

# Fetch papers and generate skeletons
arxiv-ingest run                # fetch + generate in one step

# Or step by step:
arxiv-ingest fetch              # saves data/fetched.json
arxiv-ingest generate           # creates skeleton files in output_dir
```

## Configuration (`config.yaml`)

```yaml
output_dir: "../research-wiki"  # path to your wiki directory
max_results: 20                 # papers per keyword
days_back: 7                    # look back N days

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
```

See `config.yaml.example` for the full reference with all options documented.

## Output format

Skeleton files are created at:

```
output_dir/
├── sources/{Category}/{slug}.md      # Metadata (title, authors, abstract, URL)
├── evidence/{Category}/{slug}.md     # Claims & benchmarks — fill this in
└── wiki/papers/{Category}/{slug}.md  # Synthesis & interpretation — fill this in
```

`sources/` files are written once and never touched again.
`evidence/` and `wiki/` files are only (re-)created when they still contain the unfilled template placeholder, so your edits are safe across re-runs.

## Using with Claude Code

Copy the skill file so `/arxiv-ingest` is available as a Claude Code command:

```bash
cp .claude/commands/arxiv-ingest.md ~/.claude/commands/
# or into your project's .claude/commands/
```

After running `arxiv-ingest run`, invoke `/arxiv-ingest` in Claude Code.
Claude reads each paper's abstract (and PDF when available) and fills in the `evidence/` and `wiki/` files automatically.

## GitHub Actions: daily auto-ingest

### Setup

1. Fork or use this repo as a template
2. Create a GitHub Fine-grained PAT with **Write** access to your wiki repo
3. Add to your repo's **Settings → Secrets and variables → Actions**:

   | Kind | Name | Value |
   |------|------|-------|
   | Secret | `GH_PAT` | your PAT |
   | Variable | `WIKI_REPO` | `your-name/research-wiki` |

4. Go to **Actions → Daily arXiv Ingest → Run workflow** to verify

### Schedule

- **Auto**: Mon–Fri UTC 01:00 (JST 10:00) — `cron: '0 1 * * 1-5'`
- **Manual**: `workflow_dispatch` with optional `days_back` override

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## License

MIT
