#!/usr/bin/env python3
import requests
import datetime as dt
import html
from email.utils import format_datetime
from pathlib import Path
import os

OWNER = "vllm-project"
REPO = "vllm"

# 你要订阅的所有 label（可以自行增删）
LABELS = [
    "good first issue",
    "gpt-oss",
    "moe",
]

MAX_ITEMS = 50


def label_to_slug(label: str) -> str:
    """
    用于拼文件名，例如:
      "good first issue" -> "good_first_issue"
      "gpt-oss"          -> "gpt-oss"
    """
    return (
        label.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace(":", "_")
    )


def api_url() -> str:
    return f"https://api.github.com/repos/{OWNER}/{REPO}/issues"


def fetch_issues(label: str):
    params = {
        "state": "open",
        "labels": label,
        "per_page": MAX_ITEMS,
        "sort": "created",
        "direction": "desc",
    }
    headers = {
        "Accept": "application/vnd.github+json",
    }

    # 用 GITHUB_TOKEN 提高 rate limit（由 GitHub Actions 自动注入）
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(api_url(), params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def iso_to_rfc2822(iso_str: str) -> str:
    # 例如 "2025-11-27T10:23:45Z"
    dt_obj = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return format_datetime(dt_obj)


def build_rss(label: str, issues):
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    now_str = format_datetime(now)

    feed_items = []
    for issue in issues:
        title = html.escape(issue["title"])
        link = issue["html_url"]
        guid = issue["html_url"]
        created_at = iso_to_rfc2822(issue["created_at"])
        description = issue.get("body") or ""
        if len(description) > 800:
            description = description[:800] + "\n\n..."
        description = html.escape(description)

        item = f"""  <item>
    <title>{title}</title>
    <link>{link}</link>
    <guid isPermaLink="false">{guid}</guid>
    <pubDate>{created_at}</pubDate>
    <description>{description}</description>
  </item>"""
        feed_items.append(item)

    items_str = "\n".join(feed_items)

    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>vLLM issues - label: {html.escape(label)}</title>
  <link>https://github.com/{OWNER}/{REPO}/issues</link>
  <description>Open issues with label '{html.escape(label)}' in {OWNER}/{REPO}</description>
  <language>en</language>
  <lastBuildDate>{now_str}</lastBuildDate>
{items_str}
</channel>
</rss>
"""
    return rss


def main():
    for label in LABELS:
        slug = label_to_slug(label)
        print(f"Processing label: {label} (slug={slug})")

        issues = fetch_issues(label)
        print(f"  fetched {len(issues)} issues")

        rss = build_rss(label, issues)
        feed_path = Path(f"feed_{slug}.xml")
        feed_path.write_text(rss, encoding="utf-8")
        print(f"  wrote {feed_path}")

        # 兼容老版本：good first issue 额外写一份 feed.xml
        if label == "good first issue":
            Path("feed.xml").write_text(rss, encoding="utf-8")
            print("  also wrote feed.xml (good first issue)")


if __name__ == "__main__":
    main()
