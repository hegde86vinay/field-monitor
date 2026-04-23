# Field Monitor

Daily Software Architecture digest sourced exclusively from Medium. Runs at 20:00 every day via macOS launchd, scrapes 5 fixed topics through an authenticated Playwright session, and delivers a single self-contained HTML report (saved to `reports/` and emailed to you).

## Topics

| Section | Medium tags queried |
|---|---|
| Distributed Architecture | `distributed-systems`, `microservices`, `software-architecture` |
| System Design Interviews | `system-design-interview`, `system-design`, `coding-interviews` |
| AI Use Cases | `artificial-intelligence`, `generative-ai-use-cases`, `llm`, `ai-agents` |
| Java / Spring Boot | `spring-boot`, `java`, `java-spring-boot` |
| Cloud News (AWS/Azure/GCP) | `aws`, `azure`, `google-cloud-platform`, `cloud-computing` |

Each topic returns the top 5 articles by claps, deduplicated globally across topics, filtered to the last 24 hours.

## One-time setup

```sh
cd /Users/vinayhegde/ClaudeProjects/field-monitor

# 1. venv + deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Playwright browser
python -m playwright install chromium

# 3. Non-secret config (usernames, recipient email — NO passwords)
cp .env.example .env
# Edit .env if your email differs from the default.

# 4. Stash secrets in macOS Keychain (no passwords on disk anywhere)
python scripts/store_secrets.py
#   - Medium / Google account password
#   - Gmail SMTP App Password (https://myaccount.google.com/apppasswords)

# 5. Interactive Medium login (opens a real Chrome window)
python main.py --first-login --headed
#   Click "Sign in with Google", complete password + MFA in the window,
#   then return to the terminal and press Enter.
```

Subsequent runs are headless and use the persisted login session.

## Manual usage

```sh
# Dry run: scrape + render, skip email, open HTML in browser
python main.py --dry-run --open-browser

# One topic only (fast iteration)
python main.py --topic "AI Use Cases" --dry-run

# Full run (real email)
python main.py
```

Outputs land in `reports/YYYY-MM-DD-digest.html`.

## Schedule (launchd)

```sh
cp scripts/com.vinayhegde.field-monitor.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/com.vinayhegde.field-monitor.plist

# Confirm
launchctl list | grep field-monitor

# Force-fire to validate the scheduled path end-to-end
launchctl start com.vinayhegde.field-monitor
tail -f logs/field-monitor.out logs/field-monitor.err

# Unload
launchctl unload -w ~/Library/LaunchAgents/com.vinayhegde.field-monitor.plist
```

If your Mac is asleep at 20:00, launchd fires the job on the next wake — `cron` would skip the day, which is why launchd is used.

## Where things live

| Concern | File |
|---|---|
| Topic→tag mapping, knobs | `config.py` |
| macOS Keychain wrapper | `keystore.py` |
| Playwright login + persistent context | `auth.py` |
| Per-tag scrape | `fetcher.py` |
| Orchestrator (login → fetch → dedup) | `pipeline.py` |
| HTML template | `render.py` |
| Gmail SMTP delivery | `emailer.py` |
| CLI entry point | `main.py` |
| launchd unit | `scripts/com.vinayhegde.field-monitor.plist` |
| Keychain setup script | `scripts/store_secrets.py` |
| HTML output | `reports/YYYY-MM-DD-digest.html` |
| Logs | `logs/field-monitor.{log,out,err}` |

## Failure modes (handled)

- **Auth state expired** → agent emails `[Field Monitor] Auth required — re-run with --first-login`, exits 1.
- **A tag is Cloudflare-blocked** → 60s back-off + one retry, then skip the tag and continue. Other topics still get rendered.
- **A topic has 0 fresh articles** → renders a "No new articles in last 24h" placeholder.
- **SMTP fails** → 2 retries (30s backoff), HTML is on disk regardless, logs to `logs/email-failures.log`, exits 2.

## Inspecting / rotating Keychain entries

```sh
security find-generic-password -s field-monitor -a medium_google_password
security find-generic-password -s field-monitor -a gmail_smtp_app_password

# Re-run setup to overwrite either entry
python scripts/store_secrets.py
```
