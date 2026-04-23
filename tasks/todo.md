# Task: Field Monitor — Daily Medium Digest

## Plan
- [x] Scaffold project (dirs, requirements, .env.example, .gitignore)
- [x] config.py with TOPIC_TAG_MAP and tunables
- [x] keystore.py + scripts/store_secrets.py for Keychain-backed secrets
- [x] auth.py with persistent Playwright context + first-login flow
- [x] fetcher.py: per-tag scrape, card parser, Cloudflare detection, 24h filter
- [x] pipeline.py: login → fan-out → global dedup → top-N per topic
- [x] render.py: GitHub-dark HTML with sidebar TOC, cards, summary table
- [x] emailer.py: Gmail SMTP_SSL with retries
- [x] main.py: argparse CLI (--first-login, --headed, --dry-run, --no-email, --topic, --open-browser)
- [x] scripts/com.vinayhegde.field-monitor.plist (launchd, 20:00 daily)
- [x] README.md with setup + scheduling

## Verification
- [x] Render with synthetic article fixtures → opens cleanly in browser
- [x] All Python modules import without error
- [x] plist is well-formed XML (plutil -lint passes)
- [ ] First-login interactive flow (USER-OWNED — requires real Google MFA)
- [ ] Real Medium scrape (USER-OWNED — runs after first-login)
- [ ] Email delivery (USER-OWNED — requires Gmail App Password in Keychain)
- [ ] launchd installed + force-fired (USER-OWNED — requires plist install)

## Review
- **What worked**: Reused IPL bot's CSS variable palette + sidebar IntersectionObserver pattern wholesale. macOS Keychain via `keyring` removed the need for any dotenv password handling. Pipeline shape (login once → fan out tags → dedup → render → email) maps cleanly onto the Gen AI News Agent precedent. Renamed `secrets.py` → `keystore.py` to avoid shadowing stdlib.
- **What didn't**: Deferred — full E2E proof requires the user's Google account login, which has to happen at the Mac with MFA. Cards in dry-run use synthetic fixtures.
- **Lessons captured in lessons.md**: yes (keystore naming, partial-success policy reasoning, headed-only first-login)
