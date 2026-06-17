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
peer_review: preprint
venue: ""
---

> **Peer review**: preprint

# {title}

## Facts from source
- (fill in) [source](../../../sources/{category}/{slug}.md)

## Current interpretation
(synthesis, analysis, judgment)

## Related pages
-

-> Details: [evidence](../../../evidence/{category}/{slug}.md)

## Open questions
- ?
"""

# Obsidian variant: uses [[wikilinks]] for graph view connectivity
WIKI_TEMPLATE_OBSIDIAN = """\
{marker}
---
title: "{title}"
aliases: []
created: {date_added}
updated: {date_added}
tags: {tags}
sources: [src-{arxiv_id}]
peer_review: preprint
venue: ""
---

> **Peer review**: preprint

# {title}

## Facts from source
- (fill in) [[{slug}]]

## Current interpretation
(synthesis, analysis, judgment)

## Related pages
- [[]]

-> Details: [evidence](../../../evidence/{category}/{slug}.md)

## Open questions
- ?
"""

QUARTZ_TEMPLATE = """\
---
title: "{title}"
authors: "{authors_str}"
venue: "{venue}"
year: {year}
url: "{url}"
code: ""
read_date: {date_added}
status: reading
tags:
{tags_yaml}
draft: false
---

<!-- arxiv-ingest: unfilled -->

## TL;DR

> (1~2 sentence summary here)

## 背景・問題設定

## 手法

## 実験

## 強み

## 弱み・未解決の問い

## 関連研究とのつながり

## 自分の研究・実装への示唆
"""


EVIDENCE_TEMPLATE_OBSIDIAN = """\
{marker}
---
source: src-{arxiv_id}
date_extracted: {date_added}
---

> Source paper: [[{slug}]]

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


def generate_evidence(
    paper: dict, wiki_root: Path, date_added: str, obsidian: bool = False
) -> tuple[Path, bool]:
    """Create evidence file. Skips if file exists and has already been filled in."""
    category = paper["wiki_category"]
    slug = paper["slug"]
    out = wiki_root / "evidence" / category / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and not is_template(out):
        return out, False

    template = EVIDENCE_TEMPLATE_OBSIDIAN if obsidian else EVIDENCE_TEMPLATE
    content = template.format(
        marker=_TEMPLATE_MARKER,
        arxiv_id=paper["arxiv_id"],
        title=paper["title"],
        date_added=date_added,
        slug=slug,
    )
    out.write_text(content)
    return out, True


def generate_wiki(
    paper: dict, wiki_root: Path, date_added: str, obsidian: bool = False
) -> tuple[Path, bool]:
    """Create wiki page. Skips if file exists and has already been filled in."""
    category = paper["wiki_category"]
    slug = paper["slug"]
    out = wiki_root / "wiki" / "papers" / category / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and not is_template(out):
        return out, False

    tags = [category.lower(), paper["matched_keyword"].lower().replace(" ", "-")]
    template = WIKI_TEMPLATE_OBSIDIAN if obsidian else WIKI_TEMPLATE

    content = template.format(
        marker=_TEMPLATE_MARKER,
        title=paper["title"].replace('"', '\\"'),
        date_added=date_added,
        tags=json.dumps(tags, ensure_ascii=False),
        arxiv_id=paper["arxiv_id"],
        category=category,
        slug=slug,
    )
    out.write_text(content)

    # Create figures directory for this paper
    figures_dir = wiki_root / "figures" / category / slug
    figures_dir.mkdir(parents=True, exist_ok=True)

    return out, True


def _venue_string(paper: dict) -> str:
    """Return venue string: journal_ref if available, else arXiv:ID."""
    jr = paper.get("journal_ref", "")
    arxiv_id_clean = paper["arxiv_id"].split("v")[0]
    if jr:
        return f"{jr} / arXiv:{arxiv_id_clean}"
    return f"arXiv:{arxiv_id_clean}"


def generate_quartz(
    paper: dict, wiki_root: Path, date_added: str
) -> tuple[Path, bool]:
    """Create a Quartz-compatible paper note in content/papers/{YYYY}/{slug}.md."""
    slug = paper["slug"]
    year = int(paper["published"][:4])
    out = wiki_root / "content" / "papers" / str(year) / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    if out.exists() and not is_template(out):
        return out, False

    tags = [
        paper["wiki_category"].lower(),
        paper["matched_keyword"].lower().replace(" ", "-"),
    ]
    tags_yaml = "\n".join(f"  - {t}" for t in tags)
    arxiv_id_clean = paper["arxiv_id"].split("v")[0] if "v" in paper["arxiv_id"] else paper["arxiv_id"]
    venue = _venue_string(paper)
    authors_str = ", ".join(paper["authors"][:5])

    content = QUARTZ_TEMPLATE.format(
        title=paper["title"].replace('"', '\\"'),
        authors_str=authors_str,
        venue=venue,
        year=year,
        url=paper["url"],
        date_added=date_added,
        tags_yaml=tags_yaml,
    )
    out.write_text(content)
    return out, True


def _update_recent(wiki_root: Path, paper: dict, date_added: str) -> None:
    """Append a paper entry to index/recent.md under its date section."""
    recent = wiki_root / "index" / "recent.md"
    if not recent.exists():
        return
    slug = paper["slug"]
    category = paper.get("wiki_category", "")
    title = paper["title"]
    arxiv_id = paper["arxiv_id"]
    line = f"- [{title}](../wiki/papers/{category}/{slug}.md) `{arxiv_id}` — {date_added}\n"
    content = recent.read_text()
    date_header = f"\n## {date_added}\n"
    if date_header in content:
        idx = content.index(date_header) + len(date_header)
        content = content[:idx] + line + content[idx:]
    else:
        content = content.rstrip() + f"\n{date_header}{line}"
    recent.write_text(content)


def _update_log(wiki_root: Path, papers_added: list[dict], date_added: str) -> None:
    """Append a batch of papers to log.md after the header."""
    log = wiki_root / "log.md"
    if not log.exists():
        return
    lines = [f"\n## {date_added}\n\n"]
    for p in papers_added:
        lines.append(f"- **Added**: {p['title']} (`{p['arxiv_id']}`)\n")
        lines.append(f"  - `sources/{p.get('wiki_category', '')}/{p['slug']}.md`\n")
        lines.append(f"  - `evidence/{p.get('wiki_category', '')}/{p['slug']}.md`\n")
        lines.append(f"  - `wiki/papers/{p.get('wiki_category', '')}/{p['slug']}.md`\n")
    log_content = log.read_text()
    header_end = log_content.find("\n", log_content.find("# ")) + 1
    log.write_text(log_content[:header_end] + "".join(lines) + log_content[header_end:])


def _update_peer_review(wiki_root: Path, paper: dict) -> None:
    """Append a paper to the preprint section of index/peer-review.md."""
    pr_file = wiki_root / "index" / "peer-review.md"
    if not pr_file.exists():
        return
    slug = paper["slug"]
    category = paper.get("wiki_category", "")
    title = paper["title"]
    arxiv_id = paper["arxiv_id"]
    row = f"| [{title}](../wiki/papers/{category}/{slug}.md) | {arxiv_id} |\n"
    content = pr_file.read_text()
    # Find the end of the preprint table (before next ## or end of file)
    preprint_idx = content.find("## preprint")
    if preprint_idx == -1:
        return
    # Find the next ## after preprint, or end of file
    next_section = content.find("\n## ", preprint_idx + 1)
    if next_section == -1:
        # Append at end of file
        content = content.rstrip() + "\n" + row
    else:
        # Insert before next section
        content = content[:next_section] + row + content[next_section:]
    pr_file.write_text(content)


def _would_create(paper: dict, wiki_root: Path) -> tuple[bool, bool, bool]:
    """Return (sources_new, evidence_new, wiki_new) without writing anything."""
    cat, slug = paper["wiki_category"], paper["slug"]
    src = wiki_root / "sources" / cat / f"{slug}.md"
    ev = wiki_root / "evidence" / cat / f"{slug}.md"
    wk = wiki_root / "wiki" / "papers" / cat / f"{slug}.md"
    return (
        not src.exists(),
        not ev.exists() or is_template(ev),
        not wk.exists() or is_template(wk),
    )


def main() -> None:
    from datetime import date

    dry_run = "--dry-run" in sys.argv
    summarize = "--summarize" in sys.argv
    obsidian = "--obsidian" in sys.argv
    quartz = "--quartz" in sys.argv
    limit = next(
        (int(a.split("=", 1)[1]) for a in sys.argv if a.startswith("--limit=")),
        None,
    )

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
    if limit is not None:
        fetched = fetched[:limit]
    date_added = date.today().isoformat()

    # Validate summarize dependencies early
    if summarize and not dry_run:
        try:
            from scripts.summarize import summarize as _summarize_fn
        except ImportError as e:
            console.print(f"[red]Error:[/red] {e}")
            sys.exit(1)
        import os
        if not os.environ.get("ANTHROPIC_API_KEY"):
            console.print("[red]Error:[/red] ANTHROPIC_API_KEY environment variable not set.")
            sys.exit(1)

    new_count = 0
    skipped_count = 0
    papers_added: list[dict] = []

    for paper in fetched:
        if quartz:
            # Quartz mode: generate sources + quartz file (no evidence/wiki)
            if dry_run:
                src = wiki_root / "sources" / paper["wiki_category"] / f"{paper['slug']}.md"
                s_new = not src.exists()
                year = int(paper["published"][:4])
                qpath = wiki_root / "content" / "papers" / str(year) / f"{paper['slug']}.md"
                q_new = not qpath.exists() or is_template(qpath)
                e_new = w_new = False
            else:
                _, s_new = generate_sources(paper, wiki_root, date_added)
                qpath, q_new = generate_quartz(paper, wiki_root, date_added)
                e_new = w_new = False

                # Auto-fill quartz file with LLM summary if requested
                if summarize and q_new:
                    try:
                        from scripts.summarize import fill_quartz_file
                        from scripts.summarize import summarize_quartz as _summarize_quartz_fn
                        summary_content = _summarize_quartz_fn(paper)
                        fill_quartz_file(qpath, summary_content)
                        console.print(f"[blue]∑ summarized[/blue] {paper['slug']}")
                    except Exception as exc:
                        console.print(f"[yellow]summarize failed:[/yellow] {exc}")

            if s_new or q_new:
                new_count += 1
                if not dry_run:
                    papers_added.append(paper)
                prefix = "[yellow]would create[/yellow]" if dry_run else "[green]✓ new[/green]"
                console.print(f"{prefix} {paper['slug']}")
            else:
                skipped_count += 1
                console.print(f"[dim]skip[/dim] {paper['slug']}")
        else:
            # Standard / Obsidian mode
            if dry_run:
                s_new, e_new, w_new = _would_create(paper, wiki_root)
            else:
                _, s_new = generate_sources(paper, wiki_root, date_added)
                ev_path, e_new = generate_evidence(paper, wiki_root, date_added, obsidian=obsidian)
                _, w_new = generate_wiki(paper, wiki_root, date_added, obsidian=obsidian)

                # Auto-fill evidence with LLM summary if requested
                if summarize and e_new:
                    try:
                        from scripts.summarize import fill_evidence
                        from scripts.summarize import summarize as _summarize_fn
                        summary = _summarize_fn(paper)
                        fill_evidence(paper, ev_path, summary, date_added)
                        console.print(f"[blue]∑ summarized[/blue] {paper['wiki_category']}/{paper['slug']}")
                    except Exception as exc:
                        console.print(f"[yellow]summarize failed:[/yellow] {exc}")

            if s_new or e_new or w_new:
                new_count += 1
                if not dry_run:
                    papers_added.append(paper)
                prefix = "[yellow]would create[/yellow]" if dry_run else "[green]✓ new[/green]"
                console.print(f"{prefix} {paper['wiki_category']}/{paper['slug']}")
            else:
                skipped_count += 1
                console.print(f"[dim]skip[/dim] {paper['wiki_category']}/{paper['slug']}")

    # Update index files for newly added papers
    if not dry_run and papers_added:
        for p in papers_added:
            _update_recent(wiki_root, p, date_added)
            _update_peer_review(wiki_root, p)
        _update_log(wiki_root, papers_added, date_added)

    label = "would create" if dry_run else "new"
    console.print(f"\n[bold]{new_count} {label}, {skipped_count} skipped → {wiki_root}[/bold]")
    if dry_run:
        console.print("[yellow]Dry run — no files written.[/yellow]")
    elif new_count and not summarize:
        console.print("[yellow]Tip: re-run with --summarize to auto-fill evidence via Claude.[/yellow]")
    elif new_count and summarize:
        console.print("[green]Evidence files auto-filled via Claude API.[/green]")

    # Webhook notification
    if not dry_run and new_count:
        webhook_url = config.get("webhook_url", "")
        if webhook_url:
            new_papers = [p for p in fetched if _would_create(p, wiki_root) != (False, False, False)]
            try:
                from scripts.notify import post_webhook
                post_webhook(webhook_url, fetched[:new_count], str(wiki_root))
                console.print("[green]Webhook notified.[/green]")
            except Exception as exc:
                console.print(f"[yellow]Webhook failed (non-fatal):[/yellow] {exc}")


if __name__ == "__main__":
    main()
