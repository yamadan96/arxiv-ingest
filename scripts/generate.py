"""Generate research-wiki skeleton files from fetched.json.

Creates sources/{Category}/{slug}.md for each paper.
evidence/ and wiki/ are filled in by Claude Code (see arxiv-ingest skill).
"""

import json
from pathlib import Path

import yaml
from rich.console import Console

console = Console()

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

## 概要
{abstract_short}

## メモ
- arXiv: {arxiv_id}
- キーワード: {matched_keyword}
- arXivカテゴリ: {arxiv_categories}
"""

EVIDENCE_TEMPLATE = """\
---
source: src-{arxiv_id}
date_extracted: {date_added}
---

# {title} からの抽出

## 主要な主張
- （Claude Code が論文を読んで記入）

## 主要な貢献
-

## 制限・注意点
-

## ベンチマーク結果
| ベンチマーク | スコア | 備考 |
|---|---|---|
| | | |

## 実装関連
-
"""

WIKI_TEMPLATE = """\
---
title: "{title}"
aliases: []
created: {date_added}
updated: {date_added}
tags: {tags}
sources: [src-{arxiv_id}]
---

# {title}

## ソースからの事実
- （Claude Code が論文を読んで記入） [source](../../../sources/{category}/{slug}.md)

## 現時点の解釈
（合成・分析・判断）

## 関連ページ
-

## 未解決の問い
- ?
"""


def load_config(config_path: Path) -> dict:
    with open(config_path) as f:
        return yaml.safe_load(f)


def generate_sources(paper: dict, wiki_root: Path, date_added: str) -> Path:
    category = paper["wiki_category"]
    slug = paper["slug"]
    out = wiki_root / "sources" / category / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    tags = [category.lower(), paper["matched_keyword"].lower().replace(" ", "-")]
    abstract_short = paper["abstract"][:300] + ("..." if len(paper["abstract"]) > 300 else "")
    authors_yaml = json.dumps(paper["authors"][:5], ensure_ascii=False)
    tags_yaml = json.dumps(tags, ensure_ascii=False)
    cats_yaml = json.dumps(paper["arxiv_categories"], ensure_ascii=False)

    content = SOURCES_TEMPLATE.format(
        arxiv_id=paper["arxiv_id"],
        title=paper["title"].replace('"', '\\"'),
        authors=authors_yaml,
        year=paper["published"][:4],
        url=paper["url"],
        tags=tags_yaml,
        date_added=date_added,
        abstract_short=abstract_short,
        matched_keyword=paper["matched_keyword"],
        arxiv_categories=cats_yaml,
    )
    out.write_text(content)
    return out


def generate_evidence(paper: dict, wiki_root: Path, date_added: str) -> Path:
    category = paper["wiki_category"]
    slug = paper["slug"]
    out = wiki_root / "evidence" / category / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    content = EVIDENCE_TEMPLATE.format(
        arxiv_id=paper["arxiv_id"],
        title=paper["title"],
        date_added=date_added,
    )
    out.write_text(content)
    return out


def generate_wiki(paper: dict, wiki_root: Path, date_added: str) -> Path:
    category = paper["wiki_category"]
    slug = paper["slug"]
    out = wiki_root / "wiki" / "papers" / category / f"{slug}.md"
    out.parent.mkdir(parents=True, exist_ok=True)

    tags = [category.lower(), paper["matched_keyword"].lower().replace(" ", "-")]
    tags_yaml = json.dumps(tags, ensure_ascii=False)

    content = WIKI_TEMPLATE.format(
        title=paper["title"].replace('"', '\\"'),
        date_added=date_added,
        tags=tags_yaml,
        arxiv_id=paper["arxiv_id"],
        category=category,
        slug=slug,
    )
    out.write_text(content)
    return out


def main() -> None:
    from datetime import date

    root = Path(__file__).parent.parent
    config = load_config(root / "config.yaml")
    wiki_root = (root / config.get("output_dir", "../research-wiki")).resolve()
    fetched = json.loads((root / "data" / "fetched.json").read_text())
    date_added = date.today().isoformat()

    created = []
    for paper in fetched:
        s = generate_sources(paper, wiki_root, date_added)
        e = generate_evidence(paper, wiki_root, date_added)
        w = generate_wiki(paper, wiki_root, date_added)
        created.append((paper["wiki_category"], paper["title"][:55], s.name))
        console.print(f"[green]✓[/green] {paper['wiki_category']}/{paper['slug']}")

    console.print(f"\n[bold]{len(created)} papers → {wiki_root}[/bold]")
    console.print("[yellow]Next: run /arxiv-ingest to fill evidence & wiki with Claude[/yellow]")


if __name__ == "__main__":
    main()
