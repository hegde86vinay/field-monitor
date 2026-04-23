"""Interactive one-time setup: stash Field Monitor secrets in macOS Keychain.

Run once after cloning. Uses getpass so passwords are never echoed to the
terminal or saved in shell history. Safe to re-run for rotation.
"""

from __future__ import annotations

import getpass
import sys
from pathlib import Path

# Allow running from project root or scripts/.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import keystore  # noqa: E402


def prompt_and_store(label: str, current: str | None, setter) -> bool:
    if current:
        keep = input(f"{label} already set. Keep existing? [Y/n] ").strip().lower()
        if keep in ("", "y", "yes"):
            print(f"  → kept existing {label}")
            return False
    value = getpass.getpass(f"Enter {label}: ").strip()
    if not value:
        print(f"  → empty input, skipped {label}")
        return False
    setter(value)
    print(f"  → stored {label} in Keychain")
    return True


def main() -> int:
    print("Field Monitor — Keychain setup")
    print("These values are stored in the macOS Keychain (encrypted at rest).\n")

    prompt_and_store(
        "Medium / Google account password",
        keystore.get_medium_password(),
        keystore.set_medium_password,
    )
    prompt_and_store(
        "Gmail SMTP App Password (16 chars, no spaces)",
        keystore.get_gmail_app_password(),
        keystore.set_gmail_app_password,
    )

    print("\nDone. Inspect entries with:")
    print('  security find-generic-password -s field-monitor -a medium_google_password')
    print('  security find-generic-password -s field-monitor -a gmail_smtp_app_password')
    return 0


if __name__ == "__main__":
    sys.exit(main())
