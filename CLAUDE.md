# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Nemoclaw

A personal AI email assistant that runs as an OpenClaw agent inside a NemoClaw sandbox. The agent (Nemotron LLM) checks Gmail for new emails, filters noise, summarizes important ones, and communicates with the user via the NemoClaw Telegram bridge. Users can reply to emails conversationally through Telegram.

## Architecture

```
Cron (every 2min) → check_email.py → pending_emails.json
                                            ↓
User (Telegram) ↔ NemoClaw Telegram Bridge ↔ OpenClaw Agent (Nemotron)
                                            ↓
                                     CLI Tools (Python)
                                            ↓
                                   Gmail API / SQLite DB
```

The Nemotron LLM agent is the brain — it summarizes emails and drafts replies directly (no external LLM API calls). Python CLI tools in `src/tools/` handle Gmail API interaction and database operations. The agent invokes these tools and processes their JSON output.

## Running in Sandbox

```bash
# Connect to the sandbox
nemoclaw jarvis connect

# Initial setup (install deps, init DB, register cron)
bash /sandbox/setup.sh

# Apply network policy (allows Gmail API access)
openshell policy set /sandbox/network-policy.yaml

# Start Telegram bridge (set TELEGRAM_BOT_TOKEN first)
export TELEGRAM_BOT_TOKEN=<your-token>
export ALLOWED_CHAT_IDS=<your-chat-id>
nemoclaw start

# Test via Telegram: send "check my email" to your bot
```

## CLI Tools (`src/tools/`)

All tools output JSON to stdout. Run from `/sandbox/` with `python -m src.tools.<name>`.

| Tool | Command | Purpose |
|------|---------|---------|
| check_email | `python -m src.tools.check_email [--max N]` | Fetch unread, classify, store new emails |
| list_emails | `python -m src.tools.list_emails [--limit N]` | List recent processed emails |
| get_email | `python -m src.tools.get_email --index N` | Get full details of email by index |
| send_reply | `python -m src.tools.send_reply --gmail-id ID --body-file PATH` | Send reply within thread |
| db_status | `python -m src.tools.db_status` | Show database statistics |

## Agent Configuration (`.agents/`)

- **system-prompt.md** — Agent persona, available tools, rules (always confirm before sending, never fabricate info)
- **skills/check-email.md** — Workflow for fetching and summarizing new emails
- **skills/reply-to-email.md** — Conversational reply flow: get email → user instructions → draft → confirm → send
- **skills/list-emails.md** — Workflow for listing recent emails

## Key Modules (`src/`)

- **gmail_client.py** — `GmailClient` wraps Gmail API (OAuth2 refresh token). `EmailMessage` dataclass. Handles fetch, MIME parsing, and sending replies within threads
- **classifier.py** — Rule-based email classifier (no LLM). Hardcoded sender/subject patterns + Gmail categories/labels → `should_notify` + `priority`
- **database.py** — SQLite at `/sandbox/nemoclaw.db` (configurable via `DB_PATH` env var). Tables: `processed_emails`, `state`. WAL mode, auto-migrates
- **config.py** — `Config` dataclass from env vars. Only Gmail + behavior settings (no Anthropic/Telegram config)

## Polling

A cron job (`cron/check_email_cron.sh`) runs every 2 minutes, calls `check_email.py`, and writes new emails to `/sandbox/pending_emails.json`. The agent checks this file on every user interaction and proactively notifies.

## Network Policy

The sandbox is deny-by-default. `network-policy.yaml` allows:
- `gmail.googleapis.com` (Gmail API)
- `oauth2.googleapis.com` (token refresh)
- `www.googleapis.com` (API discovery document)

Telegram API is allowed by default in NemoClaw's baseline policy.

## Setup Prerequisites

Requires a `.env` with Gmail OAuth2 credentials (see `.env.example`). Run `python setup_gmail.py` on a machine with a browser to generate the refresh token.
