"""Playwright login + persistent context for Medium (Google OAuth path)."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator

from playwright.sync_api import BrowserContext, Page, sync_playwright

from config import PAGE_TIMEOUT_MS, STORAGE_STATE, USER_DATA_DIR

log = logging.getLogger(__name__)


class AuthError(RuntimeError):
    """Raised when Medium auth state is missing or invalid."""


def _ensure_dirs() -> None:
    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def open_context(headless: bool = True) -> Iterator[tuple[BrowserContext, Page]]:
    """Yield a Playwright (context, page) using the persistent profile.

    The persistent context auto-loads cookies/localStorage from prior runs,
    so once `--first-login` succeeded, subsequent headless runs reuse the
    Medium session with no extra plumbing.
    """
    _ensure_dirs()
    with sync_playwright() as pw:
        context = pw.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=headless,
            channel="chrome",  # real Chrome binary; bypasses Cloudflare bot detection
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        # Patch automation signals on every page (incl. OAuth popups) before
        # any navigation — navigator.webdriver is the primary signal Cloudflare
        # Turnstile checks. chrome.runtime presence signals real Chrome.
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        page = context.new_page()
        try:
            yield context, page
        finally:
            context.close()


def is_logged_in(page: Page) -> bool:
    """Heuristic: navigate to /me; logged-in users land on a member URL,
    logged-out users get redirected to the marketing homepage or /signin.
    """
    try:
        page.goto("https://medium.com/me", wait_until="domcontentloaded", timeout=15_000)
    except Exception as exc:  # network/timeout
        log.warning("login probe failed: %s", exc)
        return False
    url = page.url
    return "/signin" not in url and "medium.com/me" in url or "medium.com/@" in url


def first_login_flow(page: Page) -> None:
    """Drive the Medium → Google OAuth flow. Intended for `--first-login --headed`.

    Pauses for the user to complete the Google login + any MFA / device-trust
    prompts manually (Google blocks credential autofill from automation
    reliably enough that scripted entry isn't worth the brittleness). The
    persistent profile then saves the resulting cookies for subsequent
    headless runs.
    """
    page.goto("https://medium.com/m/signin", wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
    log.info("Sign-in page opened. Click 'Sign in with Google' in the browser window.")
    log.info("Complete email + password + any MFA prompt.")
    log.info("Once you land on a Medium page (NOT a Google page), press Enter here.")
    input("Press Enter when login is complete > ")
    if not is_logged_in(page):
        raise AuthError("Login probe still fails after manual flow. Try again.")
    page.context.storage_state(path=str(STORAGE_STATE))
    log.info("Login persisted to %s and to user_data_dir.", STORAGE_STATE)
