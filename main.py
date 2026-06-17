"""arxiv-ingest CLI — fetch and scaffold arXiv papers into a research wiki."""

import shutil
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).parent


def cmd_init(args: list[str]) -> None:
    """Scaffold a new wiki directory and create config.yaml."""
    import json as _json
    obsidian = "--obsidian" in args
    quartz = "--quartz" in args
    plain_args = [a for a in args if a not in ("--obsidian", "--quartz")]
    wiki_dir = Path(plain_args[0]) if plain_args else Path("research-wiki")
    config_dest = Path("config.yaml")

    created: list[str] = []
    skipped: list[str] = []

    # config.yaml
    example = _PACKAGE_ROOT / "config.yaml.example"
    if config_dest.exists():
        skipped.append(str(config_dest))
    else:
        if example.exists():
            shutil.copy(example, config_dest)
        else:
            _write_default_config(config_dest, wiki_dir)
        _patch_output_dir(config_dest, wiki_dir)
        created.append(str(config_dest))

    # wiki directory skeleton
    categories = ["Multimodal", "Post_Training", "Reasoning", "Physical_AI",
                  "Pretraining", "Architecture"]
    for layer in ("sources", "evidence"):
        for cat in categories:
            d = wiki_dir / layer / cat
            d.mkdir(parents=True, exist_ok=True)
    for cat in categories:
        d = wiki_dir / "wiki" / "papers" / cat
        d.mkdir(parents=True, exist_ok=True)

    # Extended directories
    for extra_dir in (
        "wiki/topics", "wiki/models", "wiki/comparisons",
        "wiki/benchmarks", "wiki/engineering",
        "decisions", "figures", "index", "presentations",
    ):
        (wiki_dir / extra_dir).mkdir(parents=True, exist_ok=True)

    # data/ dir for fetched.json
    Path("data").mkdir(exist_ok=True)

    # Skeleton files (create only if missing)
    _init_skeleton_files(wiki_dir)
    created.append("skeleton files")

    # Obsidian: create .obsidian/app.json inside the wiki directory
    if obsidian:
        obsidian_dir = wiki_dir / ".obsidian"
        obsidian_dir.mkdir(exist_ok=True)
        app_json = obsidian_dir / "app.json"
        if not app_json.exists():
            app_json.write_text(_json.dumps({
                "useMarkdownLinks": False,
                "newLinkFormat": "shortest",
            }, indent=2) + "\n")
            created.append(str(app_json))
        else:
            skipped.append(str(app_json))

    # Quartz: create content/papers/ and content/templates/ directories
    if quartz:
        (wiki_dir / "content" / "papers").mkdir(parents=True, exist_ok=True)
        (wiki_dir / "content" / "templates").mkdir(parents=True, exist_ok=True)
        created.append(str(wiki_dir / "content" / "papers"))
        created.append(str(wiki_dir / "content" / "templates"))

        # Create content/index.md if it doesn't exist
        index_md = wiki_dir / "content" / "index.md"
        if not index_md.exists():
            index_md.write_text(
                "---\n"
                "title: Paper Survey\n"
                "---\n"
                "\n"
                "# Paper Survey\n"
                "\n"
                "Browse papers by [[tags]] or explore the [[graph]].\n"
            )
            created.append(str(index_md))
        else:
            skipped.append(str(index_md))

    created.append(str(wiki_dir))

    print("arxiv-ingest init complete\n")
    for p in created:
        print(f"  created  {p}")
    for p in skipped:
        print(f"  skipped  {p}  (already exists)")

    next_steps = (
        "\nNext steps:\n"
        "  1. Edit config.yaml — set your keywords\n"
    )
    if obsidian:
        next_steps += (
            f"  2. Open {wiki_dir} as an Obsidian vault\n"
            "  3. Run: arxiv-ingest run --obsidian\n"
        )
    elif quartz:
        next_steps += (
            f"  2. Configure Quartz to serve {wiki_dir}/content\n"
            "  3. Run: arxiv-ingest run --quartz\n"
        )
    else:
        next_steps += "  2. Run: arxiv-ingest run\n"
    print(next_steps)


def _init_skeleton_files(wiki_dir: Path) -> None:
    """Create skeleton index/log files if they do not already exist."""
    skeletons: dict[str, str] = {
        "log.md": (
            "# Change Log\n"
            "\n"
            "All changes are recorded here in reverse chronological order.\n"
        ),
        "wiki/index.md": (
            "# Research Wiki Index\n"
            "\n"
            "Papers and topics are grouped by theme."
            " Edit this file manually — do not sort mechanically.\n"
        ),
        "index/recent.md": "# Recently Added\n",
        "index/topics.md": (
            "# Topic Index\n"
            "\n"
            "| Topic | Page | Sources | Updated |\n"
            "|-------|------|---------|---------|"
            "\n"
        ),
        "index/models.md": (
            "# Model Index\n"
            "\n"
            "| Model | Page | Organization | Year |\n"
            "|-------|------|-------------|------|"
            "\n"
        ),
        "index/peer-review.md": (
            "# Peer-Review Status\n"
            "\n"
            "## accepted\n"
            "\n"
            "| Paper | Venue | Year |\n"
            "|-------|-------|------|\n"
            "\n"
            "## workshop\n"
            "\n"
            "| Paper | Venue | Year |\n"
            "|-------|-------|------|\n"
            "\n"
            "## under-review\n"
            "\n"
            "| Paper | Venue | Year |\n"
            "|-------|-------|------|\n"
            "\n"
            "## preprint\n"
            "\n"
            "| Paper | arXiv ID |\n"
            "|-------|----------|\n"
        ),
        "index/open-questions.md": "# Open Questions\n",
    }

    # SCHEMA.md uses {wiki_dir} substitution
    schema_content = (
        "# Research Wiki Schema\n"
        "\n"
        "This file defines the operating conventions for the entire wiki.\n"
        "\n"
        "## Directory Structure\n"
        "\n"
        "```\n"
        f"{wiki_dir}/\n"
        "├── SCHEMA.md\n"
        "├── log.md\n"
        "├── sources/{{Category}}/{{slug}}.md\n"
        "├── evidence/{{Category}}/{{slug}}.md\n"
        "├── wiki/papers/{{Category}}/{{slug}}.md\n"
        "├── wiki/topics/{{Category}}/{{slug}}.md\n"
        "├── wiki/models/{{slug}}.md\n"
        "├── wiki/comparisons/{{slug}}.md\n"
        "├── wiki/benchmarks/{{slug}}.md\n"
        "├── wiki/engineering/{{slug}}.md\n"
        "├── wiki/index.md\n"
        "├── figures/{{Category}}/{{slug}}/\n"
        "├── decisions/{{slug}}.md\n"
        "├── index/recent.md\n"
        "├── index/topics.md\n"
        "├── index/models.md\n"
        "├── index/peer-review.md\n"
        "├── index/open-questions.md\n"
        "└── presentations/{{date}}/\n"
        "```\n"
        "\n"
        "## Dedup Sentinel\n"
        "\n"
        "Files containing `<!-- arxiv-ingest: unfilled -->` are templates"
        " and will be regenerated.\n"
        "Files without this sentinel have been manually edited"
        " and will never be overwritten.\n"
        "\n"
        "## peer_review Values\n"
        "\n"
        "`accepted` | `workshop` | `under-review` | `preprint` | `n/a`\n"
        "\n"
        "## File Status Values\n"
        "\n"
        "`unprocessed` | `processed` | `stale`\n"
    )
    skeletons["SCHEMA.md"] = schema_content

    for rel_path, content in skeletons.items():
        target = wiki_dir / rel_path
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)


def _patch_output_dir(config_path: Path, wiki_dir: Path) -> None:
    text = config_path.read_text()
    lines = []
    for line in text.splitlines():
        if line.startswith("output_dir:"):
            lines.append(f'output_dir: "{wiki_dir}"')
        else:
            lines.append(line)
    config_path.write_text("\n".join(lines) + "\n")


def _write_default_config(config_path: Path, wiki_dir: Path) -> None:
    config_path.write_text(
        f'output_dir: "{wiki_dir}"\n'
        "max_results: 20\n"
        "days_back: 7\n"
        "\n"
        "keywords:\n"
        '  - "Vision-Language Model transformer"\n'
        '  - "LoRA PEFT fine-tuning language model"\n'
        '  - "large language model reasoning chain-of-thought"\n'
        "\n"
        "allowed_arxiv_categories: [cs.CV, cs.CL, cs.LG, cs.AI, cs.RO, stat.ML]\n"
        "require_primary_in: [cs.CV, cs.CL, cs.AI, cs.RO, stat.ML]\n"
        "\n"
        "category_map:\n"
        '  cs.CV: "Multimodal"\n'
        '  cs.CL: "Post_Training"\n'
        '  cs.LG: "Architecture"\n'
        '  cs.AI: "Reasoning"\n'
        '  cs.RO: "Physical_AI"\n'
        '  stat.ML: "Pretraining"\n'
    )


def cmd_status(args: list[str]) -> None:
    """Show fill progress for evidence and wiki files in the output directory."""
    import yaml
    from rich.console import Console
    from rich.table import Table

    console = Console()

    config_path = Path("config.yaml")
    if not config_path.exists():
        console.print("[red]Error:[/red] config.yaml not found. Run: arxiv-ingest init")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    wiki_root = (Path(config.get("output_dir", "research-wiki"))).resolve()
    if not wiki_root.exists():
        console.print(f"[red]Error:[/red] Wiki directory not found: {wiki_root}")
        sys.exit(1)

    from scripts.generate import _TEMPLATE_MARKER

    def _count(layer_dir: Path) -> tuple[int, int]:
        """Return (filled, unfilled) counts for a layer directory."""
        filled = unfilled = 0
        for md in layer_dir.rglob("*.md"):
            if _TEMPLATE_MARKER in md.read_text():
                unfilled += 1
            else:
                filled += 1
        return filled, unfilled

    table = Table(title=f"Wiki status — {wiki_root}")
    table.add_column("Layer", style="cyan")
    table.add_column("Filled", style="green", justify="right")
    table.add_column("Unfilled", style="yellow", justify="right")
    table.add_column("Total", justify="right")

    total_filled = total_unfilled = 0
    for layer in ("sources", "evidence", "wiki/papers"):
        layer_dir = wiki_root / layer
        if not layer_dir.exists():
            continue
        f, u = _count(layer_dir)
        total_filled += f
        total_unfilled += u
        label = layer if layer != "wiki/papers" else "wiki"
        table.add_row(label, str(f), str(u) if u else "[dim]0[/dim]", str(f + u))

    table.add_section()
    table.add_row("[bold]total[/bold]", str(total_filled), str(total_unfilled), str(total_filled + total_unfilled))
    console.print(table)

    if total_unfilled:
        console.print(f"\n[yellow]{total_unfilled} unfilled file(s) — run /arxiv-ingest in Claude Code to fill them.[/yellow]")
    else:
        console.print("\n[green]All files filled.[/green]")


def cmd_open(args: list[str]) -> None:
    """Open a paper's arXiv page in the default browser."""
    import json
    import webbrowser
    from rich.console import Console

    console = Console()

    if not args:
        console.print("[red]Error:[/red] provide an arXiv ID or slug.")
        console.print("Usage: arxiv-ingest open <arxiv-id|slug>")
        sys.exit(1)

    query = args[0].strip()

    fetched_path = Path("data/fetched.json")
    if not fetched_path.exists():
        console.print("[red]Error:[/red] data/fetched.json not found. Run 'arxiv-ingest fetch' first.")
        sys.exit(1)

    papers = json.loads(fetched_path.read_text())

    match = None
    for p in papers:
        if (query == p["arxiv_id"]
                or query == p["arxiv_id"].split("v")[0]
                or query == p["slug"]):
            match = p
            break

    if not match:
        console.print(f"[red]No paper found matching:[/red] {query}")
        console.print("Run [cyan]arxiv-ingest list[/cyan] to see available papers.")
        sys.exit(1)

    url = match["url"]
    console.print(f"Opening {match['title'][:60]}")
    console.print(f"  {url}")
    webbrowser.open(url)


def cmd_version(args: list[str]) -> None:
    """Print the installed package version."""
    try:
        from importlib.metadata import version
        print(version("arxiv-ingest"))
    except Exception:
        # Fallback: read version from pyproject.toml in the package root
        import re
        toml = _PACKAGE_ROOT / "pyproject.toml"
        if toml.exists():
            m = re.search(r'^version\s*=\s*"([^"]+)"', toml.read_text(), re.MULTILINE)
            if m:
                print(m.group(1))
                return
        print("unknown")


def cmd_list(args: list[str]) -> None:
    """List papers in data/fetched.json with optional filters."""
    import json
    import yaml
    from rich.console import Console
    from rich.table import Table

    console = Console()

    only_unfilled = "--unfilled" in args
    json_output = "--json" in args
    category_filter = next(
        (a.split("=", 1)[1] for a in args if a.startswith("--category=")), None
    )
    limit = next(
        (int(a.split("=", 1)[1]) for a in args if a.startswith("--limit=")), None
    )

    fetched_path = Path("data/fetched.json")
    if not fetched_path.exists():
        console.print("[red]Error:[/red] data/fetched.json not found. Run 'arxiv-ingest fetch' first.")
        sys.exit(1)

    papers = json.loads(fetched_path.read_text())

    if category_filter:
        papers = [p for p in papers if p.get("wiki_category", "").lower() == category_filter.lower()]

    if only_unfilled:
        config_path = Path("config.yaml")
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            wiki_root = Path(config.get("output_dir", "research-wiki")).resolve()
            from scripts.generate import is_template
            papers = [
                p for p in papers
                if is_template(wiki_root / "evidence" / p["wiki_category"] / f"{p['slug']}.md")
                or is_template(wiki_root / "wiki" / "papers" / p["wiki_category"] / f"{p['slug']}.md")
            ]

    if limit is not None:
        papers = papers[:limit]

    if json_output:
        print(json.dumps(papers, ensure_ascii=False, indent=2))
        return

    if not papers:
        console.print("[dim]No papers found.[/dim]")
        return

    title_parts = [f"{len(papers)} paper(s)"]
    if category_filter:
        title_parts.append(f"category={category_filter}")
    if only_unfilled:
        title_parts.append("unfilled only")

    table = Table(title=" · ".join(title_parts))
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Date", no_wrap=True)
    table.add_column("Title")
    table.add_column("arXiv ID", style="dim", no_wrap=True)

    for p in papers:
        table.add_row(
            p.get("wiki_category", ""),
            p.get("published", ""),
            p["title"][:70],
            p["arxiv_id"],
        )

    console.print(table)


def cmd_embed(args: list[str]) -> None:
    """Encode paper titles + abstracts and save embeddings to data/embeddings.npz."""
    import json

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print(
            "Error: sentence-transformers is required.\n"
            "Install: uv add --optional semantic sentence-transformers",
            file=sys.stderr,
        )
        sys.exit(1)

    from rich.console import Console
    console = Console()

    fetched_path = Path("data/fetched.json")
    if not fetched_path.exists():
        console.print("[red]Error:[/red] data/fetched.json not found. Run 'arxiv-ingest fetch' first.")
        sys.exit(1)

    papers = json.loads(fetched_path.read_text())
    if not papers:
        console.print("[yellow]No papers to embed.[/yellow]")
        return

    emb_path = Path("data/embeddings.npz")

    # Load existing embeddings for incremental updates
    existing_ids: set[str] = set()
    existing_id_list: list[str] = []
    existing_vectors: list = []
    if emb_path.exists():
        data = np.load(emb_path, allow_pickle=True)
        existing_id_list = list(data["paper_ids"])
        existing_vectors = list(data["embeddings"])
        existing_ids = set(existing_id_list)

    # Filter to papers not yet embedded
    new_papers = [p for p in papers if p["arxiv_id"] not in existing_ids]
    if not new_papers:
        console.print(f"[dim]All {len(papers)} papers already embedded.[/dim]")
        return

    console.print(f"Encoding {len(new_papers)} new papers (skipping {len(existing_ids)} existing)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    texts = [f"{p['title']}. {p['abstract']}" for p in new_papers]
    new_vectors = model.encode(texts, show_progress_bar=True)

    # Merge with existing
    all_ids = existing_id_list + [p["arxiv_id"] for p in new_papers]
    if existing_vectors:
        all_vectors = np.vstack([np.array(existing_vectors), new_vectors])
    else:
        all_vectors = new_vectors

    np.savez(emb_path, paper_ids=np.array(all_ids), embeddings=all_vectors)
    console.print(f"[green]Saved {len(all_ids)} embeddings → {emb_path}[/green]")


def _semantic_search(
    query: str,
    limit: int,
) -> None:
    """Run semantic similarity search against pre-computed embeddings."""
    import json

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print(
            "Error: sentence-transformers is required.\n"
            "Install: uv add --optional semantic sentence-transformers",
            file=sys.stderr,
        )
        sys.exit(1)

    from rich.console import Console
    from rich.table import Table

    console = Console()

    emb_path = Path("data/embeddings.npz")
    if not emb_path.exists():
        console.print(
            "[red]Error:[/red] data/embeddings.npz not found.\n"
            "Run: [cyan]arxiv-ingest embed[/cyan] first."
        )
        sys.exit(1)

    fetched_path = Path("data/fetched.json")
    if not fetched_path.exists():
        console.print("[red]Error:[/red] data/fetched.json not found.")
        sys.exit(1)

    data = np.load(emb_path, allow_pickle=True)
    paper_ids = list(data["paper_ids"])
    embeddings = data["embeddings"]

    papers = json.loads(fetched_path.read_text())
    id_to_paper = {p["arxiv_id"]: p for p in papers}

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_vec = model.encode([query])

    # Cosine similarity
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1, norms)  # avoid division by zero
    normed = embeddings / norms
    q_norm = query_vec / np.linalg.norm(query_vec)
    scores = (normed @ q_norm.T).flatten()

    top_indices = np.argsort(scores)[::-1][:limit]

    table = Table(title=f"Semantic search: '{query}' (top {limit})")
    table.add_column("Score", style="green", no_wrap=True, justify="right")
    table.add_column("Category", style="cyan", no_wrap=True)
    table.add_column("Title")
    table.add_column("arXiv ID", style="dim", no_wrap=True)

    for idx in top_indices:
        pid = paper_ids[idx]
        score = scores[idx]
        p = id_to_paper.get(pid)
        if p:
            table.add_row(
                f"{score:.3f}",
                p.get("wiki_category", ""),
                p["title"][:70],
                p["arxiv_id"],
            )
        else:
            table.add_row(f"{score:.3f}", "", "(paper removed from fetched.json)", pid)

    console.print(table)


def cmd_search(args: list[str]) -> None:
    """Search local wiki files for a keyword, or use --semantic for vector similarity."""
    import json
    import re
    import yaml
    from rich.console import Console
    from rich.table import Table

    console = Console()

    json_output = "--json" in args
    semantic = "--semantic" in args
    limit = next(
        (int(a.split("=", 1)[1]) for a in args if a.startswith("--limit=")), 10
    )
    plain_args = [
        a for a in args
        if a not in ("--json", "--semantic") and not a.startswith("--limit=")
    ]

    if not plain_args:
        console.print("[red]Error:[/red] provide a search term. Usage: arxiv-ingest search <term>")
        sys.exit(1)

    query = " ".join(plain_args)

    # Semantic search mode
    if semantic:
        _semantic_search(query, limit)
        return

    # Keyword search mode (original behavior)
    query_lower = query.lower()

    config_path = Path("config.yaml")
    if not config_path.exists():
        console.print("[red]Error:[/red] config.yaml not found. Run: arxiv-ingest init")
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    wiki_root = Path(config.get("output_dir", "research-wiki")).resolve()
    if not wiki_root.exists():
        console.print(f"[red]Error:[/red] Wiki directory not found: {wiki_root}")
        sys.exit(1)

    # (layer, slug, rel_path, plain_snippet, rich_snippet)
    results: list[tuple[str, str, str, str, str]] = []

    for md in sorted(wiki_root.rglob("*.md")):
        text = md.read_text()
        if query_lower not in text.lower():
            continue

        # Determine layer label from path relative to wiki_root
        rel = md.relative_to(wiki_root)
        parts = rel.parts
        layer = parts[0] if parts[0] != "wiki" else "wiki/" + parts[1]

        # Extract a short snippet around the first match
        idx = text.lower().find(query_lower)
        start = max(0, idx - 40)
        end = min(len(text), idx + len(query_lower) + 60)
        plain = text[start:end].replace("\n", " ").strip()
        rich_snippet = re.sub(
            re.escape(query_lower), f"[bold yellow]{query_lower}[/bold yellow]", plain,
            flags=re.IGNORECASE,
        )

        results.append((layer, md.stem, str(rel), plain, rich_snippet))

    if json_output:
        print(json.dumps(
            [{"layer": l, "file": slug, "path": path, "snippet": plain}
             for l, slug, path, plain, _ in results],
            ensure_ascii=False, indent=2,
        ))
        return

    if not results:
        console.print(f"No results for [bold]{query}[/bold]")
        return

    table = Table(title=f"{len(results)} result(s) for '{query}'")
    table.add_column("Layer", style="cyan", no_wrap=True)
    table.add_column("File")
    table.add_column("Snippet")

    for layer, slug, _path, _plain, rich in results:
        table.add_row(layer, slug[:50], rich[:120])

    console.print(table)


def _to_csv(papers: list[dict]) -> str:
    """Format papers as CSV (title, authors, date, category, arXiv ID, URL)."""
    import csv
    import io
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["title", "authors", "published", "category", "arxiv_id", "url", "matched_keyword"])
    for p in papers:
        writer.writerow([
            p["title"],
            "; ".join(p["authors"][:10]),
            p["published"],
            p["wiki_category"],
            p["arxiv_id"],
            p["url"],
            p["matched_keyword"],
        ])
    return out.getvalue()


def _bibtex_key(paper: dict) -> str:
    """Generate a BibTeX cite key: firstauthorYYYYfirstword."""
    if not paper["authors"]:
        first_author = "unknown"
    else:
        name = paper["authors"][0]
        # Handle "Last, First" (BibTeX style) and "First Last" (natural order)
        first_author = (name.split(",")[0] if "," in name else name.split()[-1]).strip().lower()
    year = paper["published"][:4]
    title_words = [w.lower() for w in paper["title"].split() if w.isalpha()]
    short = title_words[0] if title_words else "paper"
    return f"{first_author}{year}{short}"


def _to_bibtex(paper: dict) -> str:
    """Format a single paper as a BibTeX @misc entry."""
    key = _bibtex_key(paper)
    authors = " and ".join(paper["authors"][:10])
    year = paper["published"][:4]
    # Strip version suffix from arXiv ID for eprint field (2501.00001v1 → 2501.00001)
    eprint = paper["arxiv_id"].split("v")[0]
    primary = paper["arxiv_categories"][0] if paper["arxiv_categories"] else ""
    title = paper["title"].replace("{", r"\{").replace("}", r"\}")

    lines = [
        f"@misc{{{key},",
        f"  title        = {{{title}}},",
        f"  author       = {{{authors}}},",
        f"  year         = {{{year}}},",
        f"  eprint       = {{{eprint}}},",
        f"  archivePrefix= {{arXiv}},",
        f"  primaryClass = {{{primary}}},",
        f"  url          = {{{paper['url']}}},",
        "}",
    ]
    return "\n".join(lines)


def cmd_export(args: list[str]) -> None:
    """Export fetched papers to GitHub Issues or BibTeX."""
    import json
    import subprocess
    import yaml
    from rich.console import Console

    console = Console()

    # Parse flags
    dry_run = "--dry-run" in args
    fmt = next((a.split("=", 1)[1] for a in args if a.startswith("--format=")), "issues")
    repo = next((a for a in args if a.startswith("--repo=")), None)
    repo_arg = repo.split("=", 1)[1] if repo else None
    limit = next((int(a.split("=", 1)[1]) for a in args if a.startswith("--limit=")), None)

    fetched_path = Path("data/fetched.json")
    if not fetched_path.exists():
        console.print("[red]Error:[/red] data/fetched.json not found. Run 'arxiv-ingest fetch' first.")
        sys.exit(1)

    papers = json.loads(fetched_path.read_text())
    if limit is not None:
        papers = papers[:limit]

    # BibTeX output — no gh CLI needed
    if fmt == "bibtex":
        entries = [_to_bibtex(p) for p in papers]
        print("\n\n".join(entries))
        return

    # CSV output — no gh CLI needed
    if fmt == "csv":
        print(_to_csv(papers), end="")
        return

    # Check gh is available (issues mode only)
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        console.print("[red]Error:[/red] gh CLI not found. Install: https://cli.github.com/")
        sys.exit(1)

    # Category → label mapping
    label_map = {
        "Multimodal": "cv",
        "Post_Training": "nlp",
        "Reasoning": "ai",
        "Physical_AI": "robotics",
        "Pretraining": "ml",
        "Architecture": "ml",
    }

    created = skipped = 0
    for p in papers:
        label = label_map.get(p["wiki_category"], "arxiv")
        title = f"[{p['wiki_category']}] {p['title']}"
        body = (
            f"**arXiv**: {p['url']}\n"
            f"**Authors**: {', '.join(p['authors'][:5])}\n"
            f"**Published**: {p['published']}\n"
            f"**Categories**: {', '.join(p['arxiv_categories'])}\n\n"
            f"## Abstract\n{p['abstract'][:800]}\n\n"
            f"## Notes\n- [ ] Read\n- [ ] Evidence extracted\n- [ ] Wiki page filled\n"
        )

        if dry_run:
            console.print(f"[yellow]would create[/yellow] [{label}] {p['title'][:60]}")
            created += 1
            continue

        cmd = ["gh", "issue", "create", "--title", title, "--body", body, "--label", label]
        if repo_arg:
            cmd += ["--repo", repo_arg]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip()
            console.print(f"[green]✓[/green] {url}")
            created += 1
        else:
            console.print(f"[red]✗[/red] {p['title'][:50]} — {result.stderr.strip()}")
            skipped += 1

    label_suffix = " (dry run)" if dry_run else ""
    console.print(f"\n[bold]{created} created, {skipped} failed{label_suffix}[/bold]")
    if dry_run:
        console.print("[yellow]Re-run without --dry-run to create issues.[/yellow]")


def cmd_fetch(args: list[str]) -> None:
    from scripts.fetch import main as fetch_main
    sys.argv = ["fetch"] + args
    fetch_main()


def cmd_generate(args: list[str]) -> None:
    from scripts.generate import main as generate_main
    # Forward flags to generate via sys.argv
    gen_argv = ["generate"] + args
    sys.argv = gen_argv
    generate_main()


def cmd_run(args: list[str]) -> None:
    """Fetch + generate in one step."""
    from scripts.fetch import main as fetch_main
    from scripts.generate import main as generate_main
    sys.argv = ["fetch"] + args
    fetch_main()
    # Forward output-mode flags to generate
    gen_argv = ["generate"]
    if "--obsidian" in args:
        gen_argv.append("--obsidian")
    if "--quartz" in args:
        gen_argv.append("--quartz")
    if "--summarize" in args:
        gen_argv.append("--summarize")
    if "--dry-run" in args:
        gen_argv.append("--dry-run")
    # Forward --limit=N
    for a in args:
        if a.startswith("--limit="):
            gen_argv.append(a)
            break
    sys.argv = gen_argv
    generate_main()


def print_help() -> None:
    print(
        "arxiv-ingest — fetch and scaffold arXiv papers into a research wiki\n"
        "\n"
        "Usage:\n"
        "  arxiv-ingest init [wiki-dir]  Create config.yaml and wiki directory skeleton\n"
        "                                  --obsidian  also create .obsidian/app.json\n"
        "                                  --quartz    create content/papers/ and content/templates/\n"
        "  arxiv-ingest fetch            Fetch recent papers from arXiv (saves data/fetched.json)\n"
        "                                  --since=YYYY-MM-DD  fetch from a specific date\n"
        "  arxiv-ingest generate         Generate skeleton files from fetched.json\n"
        "                                  --obsidian   use [[wikilinks]] (Obsidian-compatible)\n"
        "                                  --quartz     output Quartz-compatible files (content/papers/YYYY/slug.md)\n"
        "                                  --summarize  auto-fill evidence via Claude API\n"
        "                                               (requires: pip install 'arxiv-ingest[summarize]'\n"
        "                                                          ANTHROPIC_API_KEY env var)\n"
        "                                  --limit=<N>  generate for at most N papers\n"
        "  arxiv-ingest run              fetch + generate in one step\n"
        "                                  --limit=<N>  generate for at most N papers\n"
        "  arxiv-ingest list             List papers in data/fetched.json\n"
        "                                  --unfilled          only show unfilled papers\n"
        "                                  --category=<name>   filter by wiki category\n"
        "                                  --limit=<N>         show at most N papers\n"
        "                                  --json              output raw JSON (pipe to jq)\n"
        "  arxiv-ingest status           Show fill progress for evidence and wiki files\n"
        "  arxiv-ingest embed            Encode paper embeddings for semantic search\n"
        "                                  (requires: pip install 'arxiv-ingest[semantic]')\n"
        "  arxiv-ingest search <term>    Search local wiki files for a keyword\n"
        "                                  --semantic          vector similarity search (requires embed first)\n"
        "                                  --limit=<N>         max results for semantic search (default 10)\n"
        "                                  --json              output raw JSON\n"
        "  arxiv-ingest export           Export fetched papers (default: GitHub Issues)\n"
        "                                  --format=bibtex    output BibTeX to stdout\n"
        "                                  --format=csv       output CSV to stdout\n"
        "                                  --limit=<N>        export at most N papers\n"
        "                                  --repo=owner/repo  GitHub Issues: target repository\n"
        "                                  --dry-run          GitHub Issues: preview without creating\n"
        "  arxiv-ingest open <id|slug>   Open a paper's arXiv page in the browser\n"
        "  arxiv-ingest version          Print the installed version\n"
        "\n"
        "Flags:\n"
        "  --dry-run   Preview what would be fetched or created without writing any files\n"
        "\n"
        "Options:\n"
        "  --help    Show this help message\n"
        "\n"
        "Quick start:\n"
        "  arxiv-ingest init\n"
        "  # edit config.yaml\n"
        "  arxiv-ingest run\n"
    )


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h", "help"):
        print_help()
        return

    cmd = args[0]
    rest = args[1:]

    commands = {
        "init": cmd_init,
        "fetch": cmd_fetch,
        "generate": cmd_generate,
        "run": cmd_run,
        "list": cmd_list,
        "status": cmd_status,
        "search": cmd_search,
        "embed": cmd_embed,
        "export": cmd_export,
        "open": cmd_open,
        "version": cmd_version,
    }

    if cmd not in commands:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print_help()
        sys.exit(1)

    commands[cmd](rest)


if __name__ == "__main__":
    main()
