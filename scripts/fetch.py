"""Fetch recent arXiv papers matching configured keywords."""

import json
import re
import sys
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


def fetch_papers(config: dict) -> list[dict]:
    client = arxiv.Client()
    cutoff = datetime.now(timezone.utc) - timedelta(days=config.get("days_back", 1))
    category_map = config.get("category_map", {})
    max_results = config.get("max_results", 20)
    allowed_cats = set(config.get("allowed_arxiv_categories", []))
    require_primary = set(config.get("require_primary_in", []))

    seen_ids: set[str] = set()
    papers: list[dict] = []

    for keyword in config.get("keywords", []):
        console.print(f"[cyan]Searching:[/cyan] {keyword}")
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
            if arxiv_id in seen_ids:
                continue
            seen_ids.add(arxiv_id)
            papers.append(
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
                }
            )

    return papers


def main() -> None:
    root = Path(__file__).parent.parent
    config_path = root / "config.yaml"
    if not config_path.exists():
        console.print(
            "[red]Error:[/red] config.yaml not found.\n"
            "Run: cp config.yaml.example config.yaml"
        )
        sys.exit(1)
    config = load_config(config_path)

    if not config.get("keywords"):
        console.print("[red]Error:[/red] No keywords defined in config.yaml.")
        sys.exit(1)

    try:
        papers = fetch_papers(config)
    except Exception as exc:
        console.print(f"[red]Error fetching papers:[/red] {exc}")
        sys.exit(1)

    out = root / "data" / "fetched.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(papers, ensure_ascii=False, indent=2))

    table = Table(title=f"Fetched {len(papers)} papers")
    table.add_column("Category", style="cyan")
    table.add_column("Title")
    table.add_column("Date")
    for p in papers:
        table.add_row(p["wiki_category"], p["title"][:60], p["published"])
    console.print(table)
    console.print(f"[green]Saved → {out}[/green]")


if __name__ == "__main__":
    main()
