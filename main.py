"""arxiv-ingest CLI — fetch and scaffold arXiv papers into a research wiki."""

import shutil
import sys
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).parent


def cmd_init(args: list[str]) -> None:
    """Scaffold a new wiki directory and create config.yaml."""
    wiki_dir = Path(args[0]) if args else Path("research-wiki")
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
        # Point output_dir at the wiki dir we're about to create
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

    # data/ dir for fetched.json
    Path("data").mkdir(exist_ok=True)

    created.append(str(wiki_dir))

    print("arxiv-ingest init complete\n")
    for p in created:
        print(f"  created  {p}")
    for p in skipped:
        print(f"  skipped  {p}  (already exists)")
    print(
        "\nNext steps:\n"
        f"  1. Edit config.yaml — set your keywords\n"
        f"  2. Run: arxiv-ingest run\n"
    )


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


def cmd_search(args: list[str]) -> None:
    """Search local wiki files for a keyword."""
    import re
    import yaml
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if not args:
        console.print("[red]Error:[/red] provide a search term. Usage: arxiv-ingest search <term>")
        sys.exit(1)

    query = " ".join(args).lower()

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

    results: list[tuple[str, str, str]] = []  # (layer, slug, snippet)

    for md in sorted(wiki_root.rglob("*.md")):
        text = md.read_text()
        if query not in text.lower():
            continue

        # Determine layer label from path relative to wiki_root
        rel = md.relative_to(wiki_root)
        parts = rel.parts
        layer = parts[0] if parts[0] != "wiki" else "wiki/" + parts[1]

        # Extract a short snippet around the first match
        idx = text.lower().find(query)
        start = max(0, idx - 40)
        end = min(len(text), idx + len(query) + 60)
        snippet = text[start:end].replace("\n", " ").strip()
        # Highlight the match
        snippet = re.sub(
            re.escape(query), f"[bold yellow]{query}[/bold yellow]", snippet,
            flags=re.IGNORECASE,
        )

        slug = md.stem
        results.append((layer, slug, snippet))

    if not results:
        console.print(f"No results for [bold]{query}[/bold]")
        return

    table = Table(title=f"{len(results)} result(s) for '{query}'")
    table.add_column("Layer", style="cyan", no_wrap=True)
    table.add_column("File")
    table.add_column("Snippet")

    for layer, slug, snippet in results:
        table.add_row(layer, slug[:50], snippet[:100])

    console.print(table)


def cmd_export(args: list[str]) -> None:
    """Export fetched papers to GitHub Issues via gh CLI."""
    import json
    import subprocess
    import yaml
    from rich.console import Console

    console = Console()

    # Parse flags
    dry_run = "--dry-run" in args
    repo = next((a for a in args if a.startswith("--repo=")), None)
    repo_arg = repo.split("=", 1)[1] if repo else None

    # Check gh is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        console.print("[red]Error:[/red] gh CLI not found. Install: https://cli.github.com/")
        sys.exit(1)

    fetched_path = Path("data/fetched.json")
    if not fetched_path.exists():
        console.print("[red]Error:[/red] data/fetched.json not found. Run 'arxiv-ingest fetch' first.")
        sys.exit(1)

    papers = json.loads(fetched_path.read_text())

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
    generate_main()


def cmd_run(args: list[str]) -> None:
    """Fetch + generate in one step."""
    from scripts.fetch import main as fetch_main
    from scripts.generate import main as generate_main
    fetch_main()
    generate_main()


def print_help() -> None:
    print(
        "arxiv-ingest — fetch and scaffold arXiv papers into a research wiki\n"
        "\n"
        "Usage:\n"
        "  arxiv-ingest init [wiki-dir]  Create config.yaml and wiki directory skeleton\n"
        "  arxiv-ingest fetch            Fetch recent papers from arXiv (saves data/fetched.json)\n"
        "                                  --since=YYYY-MM-DD  fetch from a specific date\n"
        "  arxiv-ingest generate         Generate skeleton files from fetched.json\n"
        "                                  --summarize  auto-fill evidence via Claude API\n"
        "                                               (requires: pip install 'arxiv-ingest[summarize]'\n"
        "                                                          ANTHROPIC_API_KEY env var)\n"
        "  arxiv-ingest run              fetch + generate in one step\n"
        "  arxiv-ingest status           Show fill progress for evidence and wiki files\n"
        "  arxiv-ingest search <term>    Search local wiki files for a keyword\n"
        "  arxiv-ingest export           Export fetched papers to GitHub Issues (requires gh CLI)\n"
        "                                  --repo=owner/repo  target repository\n"
        "                                  --dry-run          preview without creating\n"
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
        "status": cmd_status,
        "search": cmd_search,
        "export": cmd_export,
    }

    if cmd not in commands:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print_help()
        sys.exit(1)

    commands[cmd](rest)


if __name__ == "__main__":
    main()
