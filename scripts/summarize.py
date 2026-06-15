"""LLM-based auto-summarization of arXiv paper abstracts into evidence files."""

from __future__ import annotations

import os
from pathlib import Path

_PROMPT = """\
You are a research assistant. Given an arXiv paper's title and abstract, extract structured information.

Paper title: {title}
Abstract: {abstract}

Respond in the following plain-text format (no JSON, no markdown fences):

KEY_CLAIMS:
- <claim 1>
- <claim 2>
- <claim 3>

CONTRIBUTIONS:
- <contribution 1>
- <contribution 2>

LIMITATIONS:
- <limitation 1>
- <limitation 2>

IMPLEMENTATION_NOTES:
- <note 1>

Keep each bullet to one concise sentence. Do not add extra sections."""


def summarize(paper: dict) -> dict[str, list[str]]:
    """Call Claude API and return parsed summary sections.

    Returns a dict with keys: key_claims, contributions, limitations, implementation_notes.
    Raises ImportError if anthropic is not installed.
    Raises EnvironmentError if ANTHROPIC_API_KEY is not set.
    """
    try:
        import anthropic
    except ImportError as e:
        raise ImportError(
            "anthropic package not installed. Run: pip install 'arxiv-ingest[summarize]'"
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable not set."
        )

    client = anthropic.Anthropic(api_key=api_key)
    prompt = _PROMPT.format(title=paper["title"], abstract=paper["abstract"])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _parse(message.content[0].text)


def _parse(text: str) -> dict[str, list[str]]:
    """Parse the structured plain-text response into lists."""
    sections: dict[str, list[str]] = {
        "key_claims": [],
        "contributions": [],
        "limitations": [],
        "implementation_notes": [],
    }
    key_map = {
        "KEY_CLAIMS": "key_claims",
        "CONTRIBUTIONS": "contributions",
        "LIMITATIONS": "limitations",
        "IMPLEMENTATION_NOTES": "implementation_notes",
    }
    current: list[str] | None = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        header = line.rstrip(":")
        if header in key_map:
            current = sections[key_map[header]]
        elif line.startswith("- ") and current is not None:
            current.append(line[2:].strip())

    return sections


def fill_evidence(paper: dict, evidence_path: Path, summary: dict[str, list[str]], date_added: str) -> None:
    """Rewrite an evidence file with LLM-generated content (removes template marker)."""
    from scripts.generate import EVIDENCE_TEMPLATE, _TEMPLATE_MARKER

    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {i}" for i in items) if items else "- (none identified)"

    content = (
        f"---\n"
        f"source: src-{paper['arxiv_id']}\n"
        f"date_extracted: {date_added}\n"
        f"---\n\n"
        f"# Extracted claims: {paper['title']}\n\n"
        f"## Key claims\n{bullets(summary['key_claims'])}\n\n"
        f"## Contributions\n{bullets(summary['contributions'])}\n\n"
        f"## Limitations\n{bullets(summary['limitations'])}\n\n"
        f"## Benchmark results\n"
        f"| Benchmark | Score | Notes |\n"
        f"|-----------|-------|-------|\n"
        f"| | | |\n\n"
        f"## Implementation notes\n{bullets(summary['implementation_notes'])}\n"
    )
    evidence_path.write_text(content)
