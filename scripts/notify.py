"""Webhook notification support (Slack / Discord / generic)."""

from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError


def post_webhook(webhook_url: str, papers: list[dict], wiki_root: str) -> None:
    """POST a new-papers summary to a Slack, Discord, or generic webhook URL."""
    if not papers:
        return

    lines = [f"• [{p['wiki_category']}] {p['title'][:80]} — {p['url']}" for p in papers[:10]]
    if len(papers) > 10:
        lines.append(f"  …and {len(papers) - 10} more")

    summary = "\n".join(lines)
    header = f"📄 {len(papers)} new arXiv paper(s) ingested → `{wiki_root}`"
    text = f"{header}\n{summary}"

    if "discord.com" in webhook_url:
        payload = {"content": text}
    else:
        # Slack incoming webhook format (also works as generic)
        payload = {"text": text}

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10):
            pass
    except URLError as e:
        raise RuntimeError(f"Webhook POST failed: {e}") from e
