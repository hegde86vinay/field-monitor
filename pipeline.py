"""Orchestrator: fan-out tags → dedup → top-N per topic.

No Playwright or auth required — fetcher uses Medium's public RSS feeds.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from config import TOP_N_PER_TOPIC, TOPIC_TAG_MAP
from fetcher import Article, fetch_tag

log = logging.getLogger(__name__)


def run(only_topic: Optional[str] = None) -> dict[str, list[Article]]:
    """Fetch articles for every topic, dedup globally, return top-N per topic.

    A topic with zero fresh articles is still present with an empty list
    (the renderer shows a placeholder). Sorting is by published_at desc
    since RSS feeds don't expose clap counts.
    """
    topics = (
        {only_topic: TOPIC_TAG_MAP[only_topic]}
        if only_topic and only_topic in TOPIC_TAG_MAP
        else TOPIC_TAG_MAP
    )

    results: dict[str, list[Article]] = {t: [] for t in TOPIC_TAG_MAP}
    seen_urls: set[str] = set()

    for topic, tags in topics.items():
        collected: list[Article] = []
        for tag in tags:
            try:
                for art in fetch_tag(tag):
                    if art.url in seen_urls:
                        continue
                    seen_urls.add(art.url)
                    collected.append(art)
            except Exception as exc:
                log.error("tag=%s fetch failed: %s", tag, exc)

        # Member-only articles rank above free ones; ties broken by recency.
        collected.sort(
            key=lambda a: (
                a.is_member_only,
                a.published_at or datetime.min.replace(tzinfo=timezone.utc),
            ),
            reverse=True,
        )
        results[topic] = collected[:TOP_N_PER_TOPIC]
        log.info("topic=%r articles=%d", topic, len(results[topic]))

    return results
