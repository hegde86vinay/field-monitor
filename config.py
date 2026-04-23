"""Static configuration for Field Monitor.

All tunable knobs and topic→tag mappings live here. No secrets.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parent.resolve()
AUTH_DIR = ROOT / ".auth"
STORAGE_STATE = AUTH_DIR / "storage_state.json"
USER_DATA_DIR = AUTH_DIR / "chromium-profile"
REPORTS_DIR = ROOT / "reports"
LOGS_DIR = ROOT / "logs"

# Topic display name → list of Medium tag slugs to query.
# Each slug becomes https://medium.com/tag/{slug}/recent.
TOPIC_TAG_MAP: dict[str, list[str]] = {
    "Distributed Architecture":   ["distributed-systems", "microservices", "software-architecture"],
    "System Design Interviews":   ["system-design-interview", "system-design", "coding-interviews"],
    "AI Use Cases":               ["artificial-intelligence", "generative-ai-use-cases", "llm", "ai-agents"],
    "Java / Spring Boot":         ["spring-boot", "java", "java-spring-boot"],
    "Cloud News (AWS/Azure/GCP)": ["aws", "azure", "google-cloud-platform", "cloud-computing"],
}

WINDOW_HOURS = 24
TOP_N_PER_TOPIC = 5

# Anti-bot pacing
MIN_TAG_DELAY_SEC = 3.0
MAX_TAG_DELAY_SEC = 6.0
PAGE_TIMEOUT_MS = 30_000
SCROLL_PASSES = 4
SCROLL_PAUSE_SEC = 1.5

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Email
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_RETRY_COUNT = 2
SMTP_RETRY_BACKOFF_SEC = 30

# Keychain service name
KEYCHAIN_SERVICE = "field-monitor"
KEY_MEDIUM_PASSWORD = "medium_google_password"
KEY_GMAIL_APP_PASSWORD = "gmail_smtp_app_password"
