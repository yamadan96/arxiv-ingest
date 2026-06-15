"""arxiv-ingest CLI — fetch and scaffold arXiv papers into a research wiki."""

import sys
from pathlib import Path


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
        "  arxiv-ingest fetch     Fetch recent papers from arXiv (saves data/fetched.json)\n"
        "  arxiv-ingest generate  Generate skeleton files from fetched.json\n"
        "  arxiv-ingest run       fetch + generate in one step\n"
        "\n"
        "Options:\n"
        "  --help    Show this help message\n"
        "\n"
        "Configuration:\n"
        "  Edit config.yaml to set keywords, output_dir, and category mappings.\n"
        "  Copy config.yaml.example to config.yaml to get started.\n"
    )


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("--help", "-h", "help"):
        print_help()
        return

    cmd = args[0]
    rest = args[1:]

    commands = {
        "fetch": cmd_fetch,
        "generate": cmd_generate,
        "run": cmd_run,
    }

    if cmd not in commands:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        print_help()
        sys.exit(1)

    commands[cmd](rest)


if __name__ == "__main__":
    main()
