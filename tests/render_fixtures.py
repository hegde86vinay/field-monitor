"""Render the digest with synthetic data so the HTML can be inspected
without an actual Medium scrape. Produces reports/fixture-digest.html.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import REPORTS_DIR, TOPIC_TAG_MAP  # noqa: E402
from fetcher import Article  # noqa: E402
from render import render_html  # noqa: E402


def _mk(title: str, author: str, claps: int, mins: int, snippet: str, tag: str) -> Article:
    return Article(
        title=title,
        url=f"https://medium.com/example/{title.lower().replace(' ', '-')}",
        author=author,
        snippet=snippet,
        read_time_min=mins,
        claps=claps,
        published_at=datetime.now(timezone.utc) - timedelta(hours=2),
        source_tag=tag,
    )


def main() -> int:
    fixtures: dict[str, list[Article]] = {
        "Distributed Architecture": [
            _mk("Designing Idempotent Producers in Kafka", "Reza Shafii", 1240, 9,
                "A practical look at exactly-once semantics, transactional writes, and the trade-offs you accept when you turn idempotence on.",
                "distributed-systems"),
            _mk("Why Saga Beat 2PC at Most Shops", "Mehdi Daoudi", 880, 7,
                "Two-phase commit is dead in modern microservice fleets. Here's the reasoning, with three concrete migration patterns.",
                "microservices"),
            _mk("CRDTs in Production: A Year Later", "Nadia Eghbal", 412, 11,
                "We replaced our last-writer-wins layer with state-based CRDTs. The good, the painful, the surprising.",
                "distributed-systems"),
        ],
        "System Design Interviews": [
            _mk("System Design: URL Shortener — Beyond the Standard Answer", "Alex Xu", 3420, 14,
                "Most candidates give the same five-minute answer. Here's how to turn the same prompt into a 45-minute conversation that actually impresses.",
                "system-design-interview"),
            _mk("Rate Limiting: Token Bucket vs Sliding Window in Interviews", "Donne Martin", 1560, 8,
                "Which to reach for, when, and the follow-up questions every senior interviewer asks next.",
                "system-design"),
        ],
        "AI Use Cases": [
            _mk("RAG Is Not a Silver Bullet — Three Things to Try First", "Simon Willison", 2890, 6,
                "Before you wire up a vector DB, try these three cheaper alternatives. They solve 60% of the cases people reach for RAG to fix.",
                "llm"),
            _mk("Building an Agent That Knows When to Stop", "Jason Liu", 1170, 12,
                "Termination conditions are the underrated part of agent design. A practical framework with code.",
                "ai-agents"),
            _mk("Claude vs GPT-4o for Structured Extraction: We Ran the Numbers", "Anthropic Research", 940, 9,
                "12,000 documents, four extraction tasks, two providers. The results were not what we expected.",
                "artificial-intelligence"),
        ],
        "Java / Spring Boot": [
            _mk("Spring Boot 3.4: Virtual Threads in Anger", "Josh Long", 1820, 10,
                "We migrated a 200-rps service from platform threads to virtual threads. Six surprises and one regret.",
                "spring-boot"),
            _mk("Goodbye @Autowired: Modern DI Patterns in Spring 6", "Olga Maciaszek-Sharma", 760, 8,
                "Constructor injection is no longer a style choice — here's the reasoning the framework team is making explicit in 2026.",
                "java"),
        ],
        "Cloud News (AWS/Azure/GCP)": [
            _mk("AWS S3 Express One Zone — Real-World Latency Numbers", "Corey Quinn", 2210, 7,
                "Marketing said 10x faster. We measured P50, P99, and the cost crossover point. Here's what we found.",
                "aws"),
            _mk("Azure Container Apps vs AKS in 2026: A Decision Framework", "Microsoft Azure", 690, 11,
                "Three concrete production scenarios where each one wins. Plus the surprising tie-breaker most teams miss.",
                "azure"),
            _mk("GCP Cloud Run Now Supports Persistent Volumes — Why It Matters", "Google Cloud", 540, 5,
                "The serverless-vs-stateful debate just got more interesting. A practical look at the new feature.",
                "google-cloud-platform"),
            _mk("Multi-Cloud Egress: The Bill That Killed Our Strategy", "Last Week in AWS", 1480, 9,
                "We tried to keep workloads portable across three clouds. The egress bills made the math impossible. Here's what we did instead.",
                "cloud-computing"),
        ],
    }

    # Sanity: keys must match config (renderer iterates in dict order)
    assert list(fixtures.keys()) == list(TOPIC_TAG_MAP.keys()), "fixture topics must match config"

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "fixture-digest.html"
    html = render_html(datetime.now(), fixtures)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
