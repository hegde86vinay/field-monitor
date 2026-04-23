"""Gmail SMTP delivery of the rendered HTML digest."""

from __future__ import annotations

import logging
import smtplib
import ssl
import time
from email.message import EmailMessage

from config import (
    LOGS_DIR,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_RETRY_BACKOFF_SEC,
    SMTP_RETRY_COUNT,
)
import keystore

log = logging.getLogger(__name__)


def _plain_fallback(html: str, results_summary: str) -> str:
    return (
        "This is the plain-text fallback for the Field Monitor digest.\n"
        "Open this email in an HTML-capable client to see the full report.\n\n"
        + results_summary
    )


def send_digest(
    html: str,
    subject: str,
    sender: str,
    recipient: str,
    plain_summary: str = "",
) -> None:
    """Send `html` as the email body via Gmail SMTP_SSL.

    Retries SMTP_RETRY_COUNT times with backoff. On final failure, appends
    to logs/email-failures.log and re-raises so caller can exit nonzero.
    """
    app_password = keystore.get_gmail_app_password()
    if not app_password:
        raise keystore.MissingSecretError(
            "Gmail App Password not in Keychain. Run scripts/store_secrets.py."
        )

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(_plain_fallback(html, plain_summary))
    msg.add_alternative(html, subtype="html")

    context = ssl.create_default_context()
    last_exc: Exception | None = None
    for attempt in range(SMTP_RETRY_COUNT + 1):
        try:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30) as smtp:
                smtp.login(sender, app_password)
                smtp.send_message(msg)
            log.info("digest emailed to %s (attempt %d)", recipient, attempt + 1)
            return
        except Exception as exc:
            last_exc = exc
            log.warning("smtp attempt %d failed: %s", attempt + 1, exc)
            if attempt < SMTP_RETRY_COUNT:
                time.sleep(SMTP_RETRY_BACKOFF_SEC)

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    fail_log = LOGS_DIR / "email-failures.log"
    with fail_log.open("a") as fh:
        fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} to={recipient} err={last_exc}\n")
    raise RuntimeError(f"SMTP delivery failed after {SMTP_RETRY_COUNT + 1} attempts: {last_exc}")
