# Lessons Log

## 2026-04-23 — Avoid `secrets.py` filename in Python projects
**What happened:** Plan called for `secrets.py` as the Keychain wrapper module. Caught during implementation that this would shadow the Python stdlib `secrets` module for any code that does `import secrets` (transitive dep paths possible).
**Root cause:** Failure to consider stdlib name collision when picking a filename.
**Rule going forward:** Never name a top-level Python module after a stdlib module. Pick a non-colliding name (`keystore.py`, `vault.py`, `auth_secrets.py`). Same applies to `email.py`, `json.py`, `tokens.py`, `logging.py`, etc.

## 2026-04-23 — Partial-success policy for daily automations
**What happened:** Reflex was to abort the run if any tag failed. Realized that for an unattended daily job, killing the entire digest because one tag was Cloudflare-blocked is the wrong default — the user loses 4 topics' worth of value to surface 1 tag's error.
**Root cause:** Treating CLAUDE.md's "no laziness, find root causes" as "crash loudly on any failure".
**Rule going forward:** "No laziness" applies to root-causing the underlying bug — not to the run-time failure mode. Daily/scheduled jobs default to partial-success: log the failure, render a warning banner in the output, continue with what works. Reserve hard failure for cases where the report would be misleading without the missing piece (e.g. auth failed entirely → no report at all).

## 2026-04-23 — `--first-login` must be `--headed` only
**What happened:** Initial CLI signature accepted `--first-login --headless` as a valid combo. There's no way to complete Google's MFA / device-trust prompt in a headless browser, so the run would just hang.
**Root cause:** Conflating the steady-state run mode (headless) with the one-time setup mode (interactive).
**Rule going forward:** When a setup mode genuinely requires human input (MFA, OAuth consent, captcha), enforce that at the CLI layer with an explicit error when an incompatible flag is passed. Don't just document it — refuse it.
