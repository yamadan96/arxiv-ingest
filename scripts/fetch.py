"""Fetch recent arXiv papers matching configured keywords."""

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import arxiv
import yaml
from rich.console import Console
from rich.table import Table

console = Console()


def load_config(config_path: Path = Path("config.yaml")) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug[:80].strip("-")


def map_category(arxiv_cats: list[str], category_map: dict) -> str:
    for cat in arxiv_cats:
        primary = cat.split(".")[0] + "." + cat.split(".")[1] if "." in cat else cat
        if primary in category_map:
            return category_map[primary]
    return "Architecture"


def _fetch_keyword(
    keyword: str,
    config: dict,
) -> list[dict]:
    """Fetch papers for a single keyword. Thread-safe (no shared mutable state)."""
    client = arxiv.Client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.get("days_back", 1))
    category_map = config.get("category_map", {})
    max_results = config.get("max_results", 20)
    allowed_cats = set(config.get("allowed_arxiv_categories", []))
    require_primary = set(config.get("require_primary_in", []))

    results_list: list[dict] = []
    search = arxiv.Search(
        query=keyword,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )
    for result in client.results(search):
        if result.published < cutoff:
            continue
        if allowed_cats and not any(c in allowed_cats for c in result.categories):
            continue
        primary = result.categories[0] if result.categories else ""
        if require_primary and primary not in require_primary:
            continue
        arxiv_id = result.entry_id.split("/")[-1]
        results_list.append(
            {
                "arxiv_id": arxiv_id,
                "slug": slugify(result.title),
                "title": result.title,
                "authors": [a.name for a in result.authors],
                "abstract": result.summary.replace("\n", " "),
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "published": result.published.date().isoformat(),
                "arxiv_categories": result.categories,
                "wiki_category": map_category(result.categories, category_map),
                "matched_keyword": keyword,
                "journal_ref": result.journal_ref or "",
            }
        )
    return results_list


def fetch_papers(config: dict, *, parallel: bool = True) -> list[dict]:
    """Fetch papers for all keywords, optionally in parallel.

    When *parallel* is True (default), keywords are fetched concurrently
    using a ThreadPoolExecutor with ``min(len(keywords), 5)`` workers.
    Duplicate arXiv IDs across keywords are merged (first occurrence wins).
    """
    keywords = config.get("keywords", [])
    if not keywords:
        return []

    seen_ids: set[str] = set()
    papers: list[dict] = []

    def _dedup_extend(batch: list[dict]) -> None:
        for p in batch:
            if p["arxiv_id"] not in seen_ids:
                seen_ids.add(p["arxiv_id"])
                papers.append(p)

    if not parallel or len(keywords) == 1:
        # Sequential path (used for --dry-run or single keyword)
        for keyword in keywords:
            console.print(f"[cyan]Searching:[/cyan] {keyword}")
            batch = _fetch_keyword(keyword, config)
            _dedup_extend(batch)
            console.print(f"[green]  done:[/green] {keyword} ({len(batch)} results)")
        return papers

    # Parallel path
    max_workers = min(len(keywords), 5)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_kw = {
            executor.submit(_fetch_keyword, kw, config): kw
            for kw in keywords
        }
        for future in as_completed(future_to_kw):
            kw = future_to_kw[future]
            try:
                batch = future.result()
                _dedup_extend(batch)
                console.print(
                    f"[green]  done:[/green] {kw} ({len(batch)} results)"
                )
            except Exception as exc:
                console.print(f"[red]Error fetching '{kw}':[/red] {exc}")

    return papers


def _parse_since(argv: list[str]) -> int | None:
    """Return days_back computed from --since=YYYY-MM-DD, or None if not given."""
    for arg in argv:
        if arg.startswith("--since="):
            date_str = arg.split("=", 1)[1]
            try:
                since = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                console.print(f"[red]Error:[/red] --since must be YYYY-MM-DD, got: {date_str}")
                sys.exit(1)
            delta = datetime.now(timezone.utc) - since
            return max(1, delta.days + 1)
    return None


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    since_days = _parse_since(sys.argv)

    root = Path(__file__).parent.parent
    config_path = root / "config.yaml"
    if not config_path.exists():
        console.print(
            "[red]Error:[/red] config.yaml not found.\n"
            "Run: arxiv-ingest init"
        )
        sys.exit(1)
    config = load_config(config_path)

    if since_days is not None:
        config["days_back"] = since_days

    if not config.get("keywords"):
        console.print("[red]Error:[/red] No keywords defined in config.yaml.")
        sys.exit(1)

    try:
        papers = fetch_papers(config, parallel=not dry_run)
    except Exception as exc:
        console.print(f"[red]Error fetching papers:[/red] {exc}")
        sys.exit(1)

    title = f"{'[DRY RUN] ' if dry_run else ''}Fetched {len(papers)} papers"
    table = Table(title=title)
    table.add_column("Category", style="cyan")
    table.add_column("Title")
    table.add_column("Date")
    for p in papers:
        table.add_row(p["wiki_category"], p["title"][:60], p["published"])
    console.print(table)

    if dry_run:
        console.print("[yellow]Dry run — fetched.json not written.[/yellow]")
        return

    out = root / "data" / "fetched.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(papers, ensure_ascii=False, indent=2))
    console.print(f"[green]Saved → {out}[/green]")


if __name__ == "__main__":
    main()
