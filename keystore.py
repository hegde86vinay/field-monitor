"""Thin wrapper over `keyring` for Keychain-stored secrets.

Named `keystore.py` rather than `secrets.py` to avoid shadowing the
stdlib `secrets` module (which transitive deps may import).

Resolution order for each secret:
  1. macOS Keychain via keyring  (local runs)
  2. Environment variable        (GitHub Actions / CI)
"""

from __future__ import annotations

import os

import keyring

from config import KEY_GMAIL_APP_PASSWORD, KEY_MEDIUM_PASSWORD, KEYCHAIN_SERVICE

# Environment variable names used in GitHub Actions Secrets
_ENV_GMAIL_APP_PASSWORD = "GMAIL_APP_PASSWORD"
_ENV_MEDIUM_PASSWORD = "MEDIUM_GOOGLE_PASSWORD"


def _get(keychain_key: str, env_var: str) -> str | None:
    """Try Keychain first, fall back to environment variable."""
    try:
        value = keyring.get_password(KEYCHAIN_SERVICE, keychain_key)
        if value:
            return value
    except Exception:
        pass
    return os.environ.get(env_var) or None


def get_medium_password() -> str | None:
    return _get(KEY_MEDIUM_PASSWORD, _ENV_MEDIUM_PASSWORD)


def get_gmail_app_password() -> str | None:
    return _get(KEY_GMAIL_APP_PASSWORD, _ENV_GMAIL_APP_PASSWORD)


def set_medium_password(value: str) -> None:
    keyring.set_password(KEYCHAIN_SERVICE, KEY_MEDIUM_PASSWORD, value)


def set_gmail_app_password(value: str) -> None:
    keyring.set_password(KEYCHAIN_SERVICE, KEY_GMAIL_APP_PASSWORD, value)


class MissingSecretError(RuntimeError):
    """Raised when a required Keychain entry is absent."""
