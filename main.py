"""Field Monitor — daily Medium digest CLI entry point."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

import keystore
from auth import AuthError, first_login_flow, open_context
from config import LOGS_DIR, REPORTS_DIR, TOPIC_TAG_MAP
from emailer import send_digest
from pipeline import run as run_pipeline
from render import render_html


def _setup_logging() -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(LOGS_DIR / "field-monitor.log"),
        ],
    )


def _plain_summary(results: dict, date_str: str) -> str:
    lines = [f"Field Monitor — {date_str}", ""]
    for topic, articles in results.items():
        lines.append(f"## {topic} ({len(articles)})")
        for a in articles:
            lines.append(f"  - {a.title} — {a.author}")
            lines.append(f"    {a.url}")
        lines.append("")
    return "\n".join(lines)


def _send_alert(subject: str, body: str) -> None:
    """Best-effort alert email when the run can't proceed (e.g. auth missing).

    Skips silently if Gmail credentials aren't set up — caller has already
    logged the underlying error.
    """
    try:
        load_dotenv()
        sender = os.environ.get("GMAIL_SMTP_USER")
        recipient = os.environ.get("RECIPIENT_EMAIL", sender)
        if not sender or not recipient:
            return
        send_digest(
            html=f"<html><body><h2>{subject}</h2><pre>{body}</pre></body></html>",
            subject=subject,
            sender=sender,
            recipient=recipient,
            plain_summary=body,
        )
    except Exception as exc:
        logging.error("alert email itself failed: %s", exc)


def cmd_first_login(args: argparse.Namespace) -> int:
    log = logging.getLogger("first-login")
    if args.headless:
        log.error("--first-login requires --headed (manual MFA required)")
        return 2
    with open_context(headless=False) as (_ctx, page):
        try:
            first_login_flow(page)
        except AuthError as exc:
            log.error("%s", exc)
            return 1
    log.info("First-login complete. Subsequent runs can be headless.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    log = logging.getLogger("run")
    load_dotenv()

    sender = os.environ.get("GMAIL_SMTP_USER")
    recipient = os.environ.get("RECIPIENT_EMAIL", sender)
    if not args.dry_run and not args.no_email and not sender:
        log.error("GMAIL_SMTP_USER not set in .env — cannot email. Use --no-email to skip.")
        return 2

    try:
        results = run_pipeline(
            only_topic=args.topic if args.topic in TOPIC_TAG_MAP else None,
        )
    except keystore.MissingSecretError as exc:
        log.error("%s", exc)
        return 2

    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = REPORTS_DIR / f"{date_str}-digest.html"
    html = render_html(now, results)
    out_path.write_text(html, encoding="utf-8")
    log.info("wrote %s (%d total articles)", out_path, sum(len(v) for v in results.values()))

    if args.dry_run or args.no_email:
        log.info("email skipped (dry-run or --no-email). Open: %s", out_path)
        if args.open_browser:
            webbrowser.open(out_path.as_uri())
        return 0

    plain = _plain_summary(results, now.strftime("%A, %B %d, %Y"))
    subject = f"[Field Monitor] Software Architecture Digest — {date_str}"
    try:
        send_digest(html, subject, sender, recipient, plain_summary=plain)
    except keystore.MissingSecretError as exc:
        log.error("%s", exc)
        return 2
    except RuntimeError as exc:
        log.error("email delivery failed: %s", exc)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    _setup_logging()
    p = argparse.ArgumentParser(prog="field-monitor", description="Daily Medium digest agent")
    p.add_argument("--first-login", action="store_true", help="Interactive Medium login (use with --headed)")
    p.add_argument("--headed", action="store_true", help="Show the browser window")
    p.add_argument("--headless", action="store_true", help="Force headless even with --first-login")
    p.add_argument("--dry-run", action="store_true", help="Render HTML but skip email")
    p.add_argument("--no-email", action="store_true", help="Render HTML but skip email")
    p.add_argument("--topic", default="", help="Run only one topic by display name")
    p.add_argument("--open-browser", action="store_true", help="Open the rendered HTML in default browser (dry-run only)")
    args = p.parse_args(argv)

    if args.first_login:
        return cmd_first_login(args)
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())
