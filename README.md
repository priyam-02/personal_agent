# Jarvis

Your personal AI email assistant running as an OpenClaw agent inside a NemoClaw sandbox. Jarvis watches your Gmail inbox, summarizes important emails using Nemotron, and talks to you on Telegram. Reply to emails conversationally — at night, on the couch, wherever.

## What it does

- **Checks Gmail** for new unread emails every 2 minutes (via cron)
- **Filters out noise** — skips promotions, social, newsletters, automated mail
- **Summarizes** each important email into 2-3 sentences (Nemotron LLM)
- **Sends summaries to Telegram** via the NemoClaw Telegram bridge
- **Reply from Telegram** — tell the agent what to say, it drafts a proper reply, you confirm and it sends

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

The Nemotron LLM agent is the brain — it summarizes emails and drafts replies directly. Python CLI tools in `src/tools/` handle Gmail API interaction and database operations.

## Setup (one-time)

### 1. Google Cloud / Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g., "Jarvis")
3. Enable the **Gmail API**: APIs & Services → Library → search "Gmail API" → Enable
4. Create credentials:
   - APIs & Services → Credentials → **Create Credentials** → **OAuth 2.0 Client ID**
   - Application type: **Desktop app**
   - Download the JSON file
5. Configure OAuth consent screen:
   - User type: **External** (or Internal if using Workspace)
   - Add your email as a test user
6. Save the downloaded JSON as `client_secret.json` in this project root

### 2. Get Gmail refresh token

```bash
# Run locally (needs a browser for OAuth)
pip install google-auth-oauthlib
python setup_gmail.py
# Copy the printed GMAIL_REFRESH_TOKEN
```

### 3. Create Telegram bot

1. Open Telegram, message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`, follow the prompts, copy the **bot token**
3. Message [@userinfobot](https://t.me/userinfobot) to get your **chat ID**

### 4. Deploy to NemoClaw sandbox

```bash
# Connect to your sandbox
nemoclaw jarvis connect

# Set environment variables inside the sandbox
export GMAIL_CLIENT_ID=<your-client-id>
export GMAIL_CLIENT_SECRET=<your-client-secret>
export GMAIL_REFRESH_TOKEN=<your-refresh-token>

# Run setup (installs deps, initializes DB, registers cron)
bash /sandbox/setup.sh

# Apply network policy (allows Gmail API access)
openshell policy set /sandbox/network-policy.yaml
```

### 5. Start the Telegram bridge

```bash
export TELEGRAM_BOT_TOKEN=<your-bot-token>
export ALLOWED_CHAT_IDS=<your-chat-id>
nemoclaw start
```

## Talking to Jarvis

Interaction is conversational — just send natural language messages via Telegram:

| Say this | What happens |
|----------|-------------|
| "check my email" | Fetches new emails, summarizes important ones |
| "list emails" | Shows recent email summaries |
| "reply to #3" | Starts a reply flow for email #3 |
| "what emails have I gotten?" | Lists recent emails with status |

### Replying to emails

1. Say **"reply to #3"** (or whichever email number)
2. Jarvis confirms which email and asks what you want to say
3. Type your reply casually: `sounds good, let's do tuesday at 2pm`
4. Jarvis drafts a proper reply and shows you a preview
5. Say **"yes"** to send, **"no"** to cancel, or describe changes

## Configuration

Set these as environment variables in the sandbox:

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_EMAILS_PER_POLL` | 10 | Max emails to process per cycle |
| `SKIP_CATEGORIES` | promotions,social,updates,forums | Gmail categories to ignore |
| `GMAIL_LABELS` | INBOX | Which labels to watch |
| `DB_PATH` | /sandbox/nemoclaw.db | SQLite database path |

## Data

All data is stored in a SQLite database at `/sandbox/nemoclaw.db` inside the sandbox. This persists across agent restarts.

To reset:
```bash
rm /sandbox/nemoclaw.db
python3 -c "from src.database import get_db; get_db()"
```

## CLI Tools

All tools output JSON and can be run manually for debugging:

```bash
python -m src.tools.check_email --max 10     # Fetch and classify new emails
python -m src.tools.list_emails --limit 5     # List recent emails
python -m src.tools.get_email --index 1       # Get details of most recent email
python -m src.tools.send_reply --gmail-id ID --body-file /tmp/reply.txt
python -m src.tools.db_status                 # Show DB statistics
```

## Troubleshooting

**"Missing required env vars"** — Check that `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, and `GMAIL_REFRESH_TOKEN` are set.

**Gmail auth errors** — Your refresh token may have expired. Re-run `setup_gmail.py` locally.

**Agent not responding on Telegram** — Verify `nemoclaw start` is running and `TELEGRAM_BOT_TOKEN` / `ALLOWED_CHAT_IDS` are set correctly.

**Network errors from sandbox** — Make sure the network policy is applied: `openshell policy set /sandbox/network-policy.yaml`

**Duplicate summaries** — The SQLite DB tracks processed emails. If you see dupes, the DB may have been wiped.

## License

MIT — do whatever you want with it.
