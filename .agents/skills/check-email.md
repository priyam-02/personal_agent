# Check Email

## Trigger
- User says "check my email", "any new emails?", "check inbox", or similar
- File `/sandbox/pending_emails.json` exists (written by cron)

## Workflow

1. Run the check-email tool:
   ```
   python -m src.tools.check_email --max 10
   ```

2. Parse the JSON output.

3. If `new_emails` is empty, tell the user: "No new important emails since last check."

4. For each email in `new_emails`:
   - Read the `body_text` field
   - Summarize in 2-3 sentences:
     - Start with what action (if any) is needed
     - Include key details: who wants what, by when, any amounts/dates
     - If purely informational, say so
   - Use casual, direct tone

5. Present each email:
   ```
   [priority_icon] Email #[index]
   From: [sender]
   Subject: [subject]

   [your summary]

   To reply, say: "reply to #[index]"
   ```
   Use 🔴 for high priority, 📩 for normal.

6. End with a brief count: "That's [N] new email(s). [M] were filtered out as noise."

## Summarization Guidelines
- 2-3 sentences MAX
- Lead with action needed from the user
- Include key details: who, what, by when, amounts, dates
- If informational only (no action needed), say so
- Never include email signatures, footers, or unsubscribe info
- For calendar invites: extract event name, date/time, location
- For threads: focus on the latest message, not the full history
