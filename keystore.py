"""Thin wrapper over `keyring` for Keychain-stored secrets.

Named `keystore.py` rather than `secrets.py` to avoid shadowing the
stdlib `secrets` module (which transitive deps may import).
"""

from __future__ import annotations

import keyring

from config import KEY_GMAIL_APP_PASSWORD, KEY_MEDIUM_PASSWORD, KEYCHAIN_SERVICE


def get_medium_password() -> str | None:
    return keyring.get_password(KEYCHAIN_SERVICE, KEY_MEDIUM_PASSWORD)


def get_gmail_app_password() -> str | None:
    return keyring.get_password(KEYCHAIN_SERVICE, KEY_GMAIL_APP_PASSWORD)


def set_medium_password(value: str) -> None:
    keyring.set_password(KEYCHAIN_SERVICE, KEY_MEDIUM_PASSWORD, value)


def set_gmail_app_password(value: str) -> None:
    keyring.set_password(KEYCHAIN_SERVICE, KEY_GMAIL_APP_PASSWORD, value)


class MissingSecretError(RuntimeError):
    """Raised when a required Keychain entry is absent."""
