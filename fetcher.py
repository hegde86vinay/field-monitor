"""Per-tag fetch of Medium RSS feeds.

Medium publishes https://medium.com/feed/tag/{slug} for every tag.
These are public, unauthenticated, and not Cloudflare-protected.
No Playwright required — just feedparser + beautifulsoup for snippet cleanup.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup

from config import MAX_TAG_DELAY_SEC, MIN_TAG_DELAY_SEC, WINDOW_HOURS
import random

log = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


@dataclass
class Article:
    title: str
    url: str
    author: str
    snippet: str = ""
    read_time_min: Optional[int] = None
    claps: int = 0
    published_at: Optional[datetime] = None
    source_tag: str = ""

    def __hash__(self) -> int:
        return hash(self.url)


def _strip_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    return soup.get_text(" ", strip=True)


def _parse_published(entry: feedparser.FeedParserDict) -> Optional[datetime]:
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass
    return None


def _snippet(entry: feedparser.FeedParserDict) -> str:
    # Prefer content over summary — Medium puts the lede in content[0]
    raw = ""
    if hasattr(entry, "content") and entry.content:
        raw = entry.content[0].get("value", "")
    if not raw:
        raw = getattr(entry, "summary", "")
    text = _strip_html(raw)
    return text[:280] + "…" if len(text) > 280 else text


def fetch_tag(tag: str) -> list[Article]:
    """Fetch https://medium.com/feed/tag/{tag} and return articles within WINDOW_HOURS.

    Returns empty list on any error — caller logs and continues.
    """
    feed_url = f"https://medium.com/feed/tag/{tag}"
    log.info("rss fetch tag=%s", tag)

    # Use requests so macOS Python gets certifi's cert bundle (stdlib urllib
    # doesn't use the system trust store on macOS without /Applications/Python*/
    # Install Certificates.command having been run).
    try:
        resp = requests.get(feed_url, headers=_HEADERS, timeout=20)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
    except requests.RequestException as exc:
        log.warning("tag=%s http error: %s", tag, exc)
        return []

    if feed.get("bozo") and not feed.entries:
        log.warning("tag=%s rss parse error: %s", tag, feed.get("bozo_exception"))
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(hours=WINDOW_HOURS)
    articles: list[Article] = []

    for entry in feed.entries:
        published_at = _parse_published(entry)
        if published_at is None or published_at < cutoff:
            continue

        url = getattr(entry, "link", "").split("?")[0]
        if not url:
            continue

        title = getattr(entry, "title", "").strip()
        author = getattr(entry, "author", "Unknown").strip()
        snippet = _snippet(entry)

        articles.append(
            Article(
                title=title,
                url=url,
                author=author,
                snippet=snippet,
                published_at=published_at,
                source_tag=tag,
            )
        )

    log.info("tag=%s entries=%d fresh=%d", tag, len(feed.entries), len(articles))
    time.sleep(random.uniform(MIN_TAG_DELAY_SEC / 3, MAX_TAG_DELAY_SEC / 3))  # polite pacing
    return articles
