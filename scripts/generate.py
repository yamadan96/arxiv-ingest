"""Generate research-wiki skeleton files from fetched.json.

Creates three files per paper:
  sources/{Category}/{slug}.md   -- immutable metadata
  evidence/{Category}/{slug}.md  -- claims/benchmarks (fill this in)
  wiki/papers/{Category}/{slug}.md -- synthesis (fill this in)

Already-filled evidence/wiki files are never overwritten.
"""

import json
import sys
from pathlib import Path

import yaml
from rich.console import Console

console = Console()

# Sentinel string embedded in unfilled template files.
# Any file that still contains this string has not been filled in yet.
_TEMPLATE_MARKER = "<!-- arxiv-ingest: unfilled -->"

SOURCES_TEMPLATE = """\
---
id: src-{arxiv_id}
title: "{title}"
authors: {authors}
year: {year}
url: "{url}"
type: paper
peer_review: preprint
venue: ""
tags: {tags}
date_added: {date_added}
status: unprocessed
---

# {title}

## Abstract
{abstract_short}

## Notes
- arXiv: {arxiv_id}
- Matched keyword: {matched_keyword}
- arXiv categories: {arxiv_categories}
"""

EVIDENCE_TEMPLATE = """\
{marker}
---
source: src-{arxiv_id}
date_extracted: {date_added}
---

# Extracted claims: {title}

## Key claims
- (fill in)

## Contributions
-

## Limitations
-

## Benchmark results
| Benchmark | Score | Notes |
|-----------|-------|-------|
| | | |

## Implementation notes
-
"""

WIKI_TEMPLATE = """\
{marker}
---
title: "{title}"
aliases: []
created: {date_added}
updated: {date_added}
tags: {tags}
sources: [src-{arxiv_id}]
---

# {title}

## Facts from source
- (fill in) [source](../../../sources/{category}/{slug}.md)

## Current interpretation
(synthesis, analysis, judgment)

## Related pages
-

## Open questions
- ?
"""


def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        console.print(
            f"[red]Error:[/red] config file not found: {config_path}\n"
            "Run: cp config.yaml.example config.yaml"
        )
        sys.exit(1)
    with open(config_path) as f:
        return yaml.safe_load(f)


def is_template(path: Path) -> bool:
    """Return True if the file still contains the unfilled template marker."""
    return path.exists() and _TEMPLATE_MARKER in path.read_text()


def generate_sources(paper: dict, wiki_root: Path, date_added: str) -> tuple[Path, bool]:
    """Create sources file. Never overwrites — sources are immutable once written."""
    category = paper["wiki_category"]
    slug = paper["slug"]
    out = wiki_root / "sources" / category / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists():
        return out, False

    tags = [category.lower(), paper["matched_keyword"].lower().replace(" ", "-")]
    abstract_short = paper["abstract"][:300] + ("..." if len(paper["abstract"]) > 300 else "")

    content = SOURCES_TEMPLATE.format(
        arxiv_id=paper["arxiv_id"],
        title=paper["title"].replace('"', '\\"'),
        authors=json.dumps(paper["authors"][:5], ensure_ascii=False),
        year=paper["published"][:4],
        url=paper["url"],
        tags=json.dumps(tags, ensure_ascii=False),
        date_added=date_added,
        abstract_short=abstract_short,
        matched_keyword=paper["matched_keyword"],
        arxiv_categories=json.dumps(paper["arxiv_categories"], ensure_ascii=False),
    )
    out.write_text(content)
    return out, True


def generate_evidence(paper: dict, wiki_root: Path, date_added: str) -> tuple[Path, bool]:
    """Create evidence file. Skips if file exists and has already been filled in."""
    category = paper["wiki_category"]
    slug = paper["slug"]
    out = wiki_root / "evidence" / category / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and not is_template(out):
        return out, False

    content = EVIDENCE_TEMPLATE.format(
        marker=_TEMPLATE_MARKER,
        arxiv_id=paper["arxiv_id"],
        title=paper["title"],
        date_added=date_added,
    )
    out.write_text(content)
    return out, True


def generate_wiki(paper: dict, wiki_root: Path, date_added: str) -> tuple[Path, bool]:
    """Create wiki page. Skips if file exists and has already been filled in."""
    category = paper["wiki_category"]
    slug = paper["slug"]
    out = wiki_root / "wiki" / "papers" / category / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and not is_template(out):
        return out, False

    tags = [category.lower(), paper["matched_keyword"].lower().replace(" ", "-")]

    content = WIKI_TEMPLATE.format(
        marker=_TEMPLATE_MARKER,
        title=paper["title"].replace('"', '\\"'),
        date_added=date_added,
        tags=json.dumps(tags, ensure_ascii=False),
        arxiv_id=paper["arxiv_id"],
        category=category,
        slug=slug,
    )
    out.write_text(content)
    return out, True


def main() -> None:
    from datetime import date

    root = Path(__file__).parent.parent
    config = load_config(root / "config.yaml")

    fetched_path = root / "data" / "fetched.json"
    if not fetched_path.exists():
        console.print(
            "[red]Error:[/red] data/fetched.json not found. Run 'arxiv-ingest fetch' first."
        )
        sys.exit(1)

    wiki_root = (root / config.get("output_dir", "../research-wiki")).resolve()
    fetched = json.loads(fetched_path.read_text())
    date_added = date.today().isoformat()

    new_count = 0
    skipped_count = 0
    for paper in fetched:
        _, s_new = generate_sources(paper, wiki_root, date_added)
        _, e_new = generate_evidence(paper, wiki_root, date_added)
        _, w_new = generate_wiki(paper, wiki_root, date_added)
        if s_new or e_new or w_new:
            new_count += 1
            console.print(f"[green]✓ new[/green] {paper['wiki_category']}/{paper['slug']}")
        else:
            skipped_count += 1
            console.print(f"[dim]skip[/dim] {paper['wiki_category']}/{paper['slug']}")

    console.print(f"\n[bold]{new_count} new, {skipped_count} skipped → {wiki_root}[/bold]")
    if new_count:
        console.print("[yellow]Next: run /arxiv-ingest to fill evidence & wiki with Claude[/yellow]")


if __name__ == "__main__":
    main()
