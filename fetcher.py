"""Per-tag fetch of Medium RSS feeds.

Medium publishes https://medium.com/feed/tag/{slug} for every tag.
These are public, unauthenticated, and not Cloudflare-protected.
No Playwright required — just feedparser + beautifulsoup for snippet cleanup.

Filters applied per article:
  - English-only: langdetect on title + snippet (drops non-English articles)
  - Member-only signal: detected from RSS content markers; used for ranking
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import requests
from bs4 import BeautifulSoup
from langdetect import DetectorFactory, LangDetectException, detect

from config import MAX_TAG_DELAY_SEC, MIN_TAG_DELAY_SEC, WINDOW_HOURS

# Make langdetect deterministic across runs
DetectorFactory.seed = 0

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
    is_member_only: bool = False

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
    raw = ""
    if hasattr(entry, "content") and entry.content:
        raw = entry.content[0].get("value", "")
    if not raw:
        raw = getattr(entry, "summary", "")
    text = _strip_html(raw)
    return text[:280] + "…" if len(text) > 280 else text


def _is_english(title: str, snippet: str) -> bool:
    """Return True if the article is detected as English.

    Uses title + snippet together for a stronger signal. Treats detection
    failures (text too short / ambiguous) as English to avoid false drops.
    """
    text = f"{title} {snippet}".strip()
    if len(text) < 20:
        return True  # too short to detect reliably — give benefit of the doubt
    try:
        return detect(text) == "en"
    except LangDetectException:
        return True


def _is_member_only(entry: feedparser.FeedParserDict) -> bool:
    """Detect Medium's member-only marker from RSS content.

    Medium includes a lock-icon SVG and/or the text 'Member-only story'
    in the content:encoded block of paywalled articles.
    """
    raw = ""
    if hasattr(entry, "content") and entry.content:
        raw = entry.content[0].get("value", "")
    if not raw:
        raw = getattr(entry, "summary", "")

    lower = raw.lower()
    return "member-only story" in lower or "member only story" in lower or 'aria-label="member' in lower


def fetch_tag(tag: str) -> list[Article]:
    """Fetch https://medium.com/feed/tag/{tag} and return English articles within WINDOW_HOURS.

    Applies:
      - 24h recency filter
      - English-only filter via langdetect
      - member-only detection (stored on Article for ranking, not filtered out)

    Returns empty list on any error — caller logs and continues.
    """
    feed_url = f"https://medium.com/feed/tag/{tag}"
    log.info("rss fetch tag=%s", tag)

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
    dropped_lang = 0

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
        member_only = _is_member_only(entry)

        if not _is_english(title, snippet):
            log.debug("tag=%s dropped non-English: %r", tag, title[:60])
            dropped_lang += 1
            continue

        articles.append(
            Article(
                title=title,
                url=url,
                author=author,
                snippet=snippet,
                published_at=published_at,
                source_tag=tag,
                is_member_only=member_only,
            )
        )

    log.info(
        "tag=%s entries=%d fresh=%d dropped_lang=%d member_only=%d",
        tag,
        len(feed.entries),
        len(articles),
        dropped_lang,
        sum(1 for a in articles if a.is_member_only),
    )
    time.sleep(random.uniform(MIN_TAG_DELAY_SEC / 3, MAX_TAG_DELAY_SEC / 3))
    return articles
