#!/usr/bin/env python3
import requests
import datetime as dt
import html
from email.utils import format_datetime
from pathlib import Path

OWNER = "vllm-project"
REPO = "vllm"
LABEL = "good first issue"
MAX_ITEMS = 50
OUTPUT_FILE = Path("feed.xml")

API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/issues"


def fetch_issues():
    params = {
        "state": "open",
        "labels": LABEL,
        "per_page": MAX_ITEMS,
        "sort": "created",
        "direction": "desc",
    }
    headers = {
        "Accept": "application/vnd.github+json",
    }
    # 使用 GITHUB_TOKEN 提高 rate limit（由 GitHub Actions 注入）
    import os

    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    resp = requests.get(API_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()


def iso_to_rfc2822(iso_str: str) -> str:
    # 例如 "2025-11-27T10:23:45Z"
    dt_obj = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return format_datetime(dt_obj)


def build_rss(issues):
    now = dt.datetime.utcnow().replace(tzinfo=dt.timezone.utc)
    now_str = format_datetime(now)

    feed_items = []
    for issue in issues:
        title = html.escape(issue["title"])
        link = issue["html_url"]
        guid = issue["html_url"]
        created_at = iso_to_rfc2822(issue["created_at"])
        description = issue.get("body") or ""
        # 简单截断一下内容，避免太长
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
  <title>vLLM good first issues</title>
  <link>https://github.com/{OWNER}/{REPO}/issues</link>
  <description>Open issues with label '{LABEL}' in {OWNER}/{REPO}</description>
  <language>en</language>
  <lastBuildDate>{now_str}</lastBuildDate>
{items_str}
</channel>
</rss>
"""
    return rss


def main():
    issues = fetch_issues()
    rss = build_rss(issues)
    OUTPUT_FILE.write_text(rss, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE} with {len(issues)} items")


if __name__ == "__main__":
    main()
