"""Unit tests for English-only and member-only filters in fetcher.py.

Positive cases: confirm articles that should pass the filter do pass.
Negative cases: confirm articles that should be rejected are rejected.
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from fetcher import _is_english, _is_member_only


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _entry(summary: str = "", content_value: str = "") -> SimpleNamespace:
    """Build a minimal feedparser-like entry object."""
    entry = SimpleNamespace()
    entry.summary = summary
    entry.content = [{"value": content_value}] if content_value else []
    return entry


# ---------------------------------------------------------------------------
# _is_english — positive cases (should return True)
# ---------------------------------------------------------------------------

class TestIsEnglishPositive:
    def test_plain_english_title_and_snippet(self):
        assert _is_english(
            "Designing Idempotent Producers in Kafka",
            "A practical look at exactly-once semantics and transactional writes.",
        )

    def test_technical_english_with_acronyms(self):
        assert _is_english(
            "AWS S3 Express One Zone — Real-World Latency Numbers",
            "We measured P50, P99, and the cost crossover point across regions.",
        )

    def test_english_with_code_terms(self):
        assert _is_english(
            "Spring Boot 3.4: Virtual Threads in Anger",
            "We migrated a 200-rps service from platform threads to virtual threads.",
        )

    def test_short_text_treated_as_english(self):
        # Text under 20 chars is too short for reliable detection — treated as English
        assert _is_english("Go", "")

    def test_empty_snippet_english_title(self):
        assert _is_english("Building a Rate Limiter in Python", "")

    def test_mixed_code_and_english(self):
        assert _is_english(
            "Why Saga Beat 2PC at Most Shops",
            "Two-phase commit is dead. Here are three migration patterns.",
        )


# ---------------------------------------------------------------------------
# _is_english — negative cases (should return False)
# ---------------------------------------------------------------------------

class TestIsEnglishNegative:
    def test_chinese_title_and_snippet(self):
        assert not _is_english(
            "分布式系统中的一致性问题",
            "在分布式系统中，一致性是最难解决的问题之一。本文探讨了常见的解决方案。",
        )

    def test_hindi_title_and_snippet(self):
        assert not _is_english(
            "माइक्रोसर्विस आर्किटेक्चर",
            "माइक्रोसर्विस आर्किटेक्चर में सेवाओं को छोटे स्वतंत्र घटकों में विभाजित किया जाता है।",
        )

    def test_spanish_article(self):
        assert not _is_english(
            "Diseño de sistemas distribuidos modernos",
            "En este artículo exploramos los patrones más importantes para construir sistemas escalables.",
        )

    def test_portuguese_article(self):
        assert not _is_english(
            "Arquitetura de Microsserviços na Prática",
            "Neste artigo vamos explorar como construir microsserviços resilientes com Spring Boot.",
        )

    def test_japanese_article(self):
        assert not _is_english(
            "分散システムの設計パターン",
            "分散システムを設計する際に重要なパターンについて解説します。",
        )

    def test_korean_article(self):
        assert not _is_english(
            "마이크로서비스 아키텍처 설계",
            "마이크로서비스 아키텍처는 현대 소프트웨어 개발의 핵심 패턴입니다.",
        )


# ---------------------------------------------------------------------------
# _is_member_only — positive cases (should return True)
# ---------------------------------------------------------------------------

class TestIsMemberOnlyPositive:
    def test_member_only_story_in_summary(self):
        entry = _entry(summary="<p>Member-only story</p><p>This article explores...</p>")
        assert _is_member_only(entry)

    def test_member_only_story_in_content(self):
        entry = _entry(content_value="<p>Member-only story</p><p>Advanced Kafka patterns...</p>")
        assert _is_member_only(entry)

    def test_member_only_case_insensitive(self):
        entry = _entry(summary="<p>MEMBER-ONLY STORY — Premium content</p>")
        assert _is_member_only(entry)

    def test_member_only_without_hyphen(self):
        entry = _entry(summary="<p>member only story</p>")
        assert _is_member_only(entry)

    def test_aria_label_member_in_content(self):
        entry = _entry(content_value='<button aria-label="member exclusive">🔒</button><p>Content...</p>')
        assert _is_member_only(entry)

    def test_content_preferred_over_summary(self):
        # content has the marker, summary does not — should still detect it
        entry = _entry(
            summary="<p>A great article about distributed systems.</p>",
            content_value="<p>Member-only story</p><p>A great article about distributed systems.</p>",
        )
        assert _is_member_only(entry)


# ---------------------------------------------------------------------------
# _is_member_only — negative cases (should return False)
# ---------------------------------------------------------------------------

class TestIsMemberOnlyNegative:
    def test_free_article_no_markers(self):
        entry = _entry(summary="<p>An open article about microservices patterns.</p>")
        assert not _is_member_only(entry)

    def test_empty_entry(self):
        entry = _entry()
        assert not _is_member_only(entry)

    def test_article_mentioning_member_in_different_context(self):
        # "member" appears but not as the Medium paywall marker
        entry = _entry(
            summary="<p>Join as a team member to contribute to open source projects.</p>"
        )
        assert not _is_member_only(entry)

    def test_free_article_with_rich_content(self):
        entry = _entry(
            content_value=(
                "<h2>Designing Idempotent Producers</h2>"
                "<p>Exactly-once semantics require careful coordination.</p>"
                "<p>Continue reading on Medium.</p>"
            )
        )
        assert not _is_member_only(entry)

    def test_summary_only_no_content(self):
        entry = _entry(summary="<p>Practical guide to rate limiting with token buckets.</p>")
        assert not _is_member_only(entry)

    def test_partial_word_match_does_not_trigger(self):
        # "membership" should not trigger the member-only check
        entry = _entry(summary="<p>Medium membership gives access to premium stories.</p>")
        assert not _is_member_only(entry)
