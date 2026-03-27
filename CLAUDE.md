# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Jarvis

A personal AI email assistant that runs as an OpenClaw agent inside a NemoClaw sandbox. The agent (Nemotron LLM) checks Gmail for new emails, filters noise, summarizes important ones, and communicates with the user via the NemoClaw Telegram bridge. Users can reply to emails conversationally through Telegram.

## Architecture

```
email_poller.py (every 2min) → Telegram notification + pending_emails.json
                                            ↓
User (Telegram) ↔ NemoClaw Telegram Bridge ↔ OpenClaw Agent (Nemotron)
                                            ↓
                                     CLI Tools (Python)
                                            ↓
                                   Gmail API / SQLite DB
```

The Nemotron LLM agent is the brain — it summarizes emails and drafts replies directly (no external LLM API calls). Python CLI tools in `src/tools/` handle Gmail API interaction and database operations. The agent invokes these tools and processes their JSON output.

**Reply safeguard**: Sending replies is a two-step process — `stage_reply` prepares a draft and returns a confirmation token, `confirm_send` requires that token to actually send. This makes it structurally impossible for the agent to send without showing the draft to the user first.

**Conversation context**: All tools automatically track which emails are discussed in the DB `state` table. This enables natural references like "reply to that email" instead of requiring `#N` indexes.

## Running in Sandbox

```bash
# Connect to the sandbox
nemoclaw jarvis connect

# Initial setup (install deps, init DB)
bash /sandbox/setup.sh

# Apply network policy from HOST machine (not inside sandbox)
openshell policy set /sandbox/network-policy.yaml

# Start the email poller (inside sandbox)
bash cron/start_poller.sh

# Start Telegram bridge from HOST machine
# SANDBOX_NAME is required (workaround for GitHub Issue #445)
export TELEGRAM_BOT_TOKEN=<your-token>
export ALLOWED_CHAT_IDS=<your-chat-id>
export SANDBOX_NAME=jarvis
nemoclaw start

# Test via Telegram: send "check my email" to your bot
```

## Known Issues

- **httplib2 ignores HTTPS_PROXY**: Gmail auth uses `requests`-based transport (`AuthorizedSession` + `_RequestsHttpShim`) instead of default httplib2 to work with the sandbox proxy at `http://10.200.0.1:3128`.
- **Telegram bridge "sandbox not found"**: Set `SANDBOX_NAME=jarvis` env var before `nemoclaw start` (GitHub Issue #445).
- **PyPI access**: May need TUI approval (`openshell term`) for first pip install even with pypi in network policy.

## CLI Tools (`src/tools/`)

All tools output JSON to stdout. Run from `/sandbox/` with `python -m src.tools.<name>`.

| Tool | Command | Purpose |
|------|---------|---------|
| check_email | `python -m src.tools.check_email [--max N]` | Fetch unread, classify, store new emails |
| list_emails | `python -m src.tools.list_emails [--limit N]` | List recent processed emails |
| get_email | `python -m src.tools.get_email --index N` | Get full details of email by index |
| get_email | `python -m src.tools.get_email --gmail-id ID` | Get email by Gmail ID |
| get_email | `python -m src.tools.get_email --search "query"` | Search emails by sender/subject/snippet |
| resolve_email | `python -m src.tools.resolve_email --query "..."` | Resolve natural email references ("that email", "from Sarah") |
| stage_reply | `python -m src.tools.stage_reply --gmail-id ID --body-file PATH` | Stage a reply draft (does NOT send) |
| confirm_send | `python -m src.tools.confirm_send --confirm-token TOKEN` | Send a staged reply (requires token) |
| db_status | `python -m src.tools.db_status` | Show database statistics |

## Agent Configuration (`.agents/`)

- **system-prompt.md** — Agent persona, available tools, two-step send rules, natural reference rules
- **skills/check-email.md** — Workflow for fetching and summarizing new emails
- **skills/reply-to-email.md** — Two-step reply flow: resolve email → draft → stage → user confirms → send
- **skills/list-emails.md** — Workflow for listing recent emails

## Key Modules (`src/`)

- **gmail_client.py** — `GmailClient` wraps Gmail API (OAuth2 refresh token). `EmailMessage` dataclass. Handles fetch, MIME parsing, and sending replies within threads
- **classifier.py** — Rule-based email classifier (no LLM). Hardcoded sender/subject patterns + Gmail categories/labels → `should_notify` + `priority`
- **database.py** — SQLite at `/sandbox/nemoclaw.db` (configurable via `DB_PATH` env var). Tables: `processed_emails`, `state`. WAL mode, auto-migrates. Includes `search_emails()` and conversation context tracking via `state` table
- **config.py** — `Config` dataclass from env vars. Only Gmail + behavior settings
- **email_poller.py** — Background daemon that polls Gmail every 2min and sends Telegram notifications for new emails

## Polling & Notifications

A background poller (`src/email_poller.py`) runs every 2 minutes, fetches new emails, and sends Telegram notifications directly via the Bot API. It also writes to `/sandbox/pending_emails.json` as a fallback for the agent. Start with `bash cron/start_poller.sh`.

## Network Policy

The sandbox is deny-by-default. `network-policy.yaml` allows:
- `gmail.googleapis.com` (Gmail API)
- `oauth2.googleapis.com` (token refresh)
- `www.googleapis.com` (API discovery document)

Telegram API is allowed by default in NemoClaw's baseline policy.

## Setup Prerequisites

Requires a `.env` with Gmail OAuth2 credentials (see `.env.example`). Run `python setup_gmail.py` on a machine with a browser to generate the refresh token. The poller also needs `TELEGRAM_BOT_TOKEN` and `ALLOWED_CHAT_IDS` in `.env`.
