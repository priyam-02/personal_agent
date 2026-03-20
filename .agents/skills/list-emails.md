# List Emails

## Trigger
- User says "list emails", "show recent emails", "what emails have I gotten?", or similar
- User asks about email status or history

## Workflow

1. Run:
   ```
   python -m src.tools.list_emails --limit 10
   ```

2. Parse the JSON output.

3. If no emails, tell the user: "No emails processed yet. Say 'check email' to fetch new ones."

4. Present emails in a clean list:
   ```
   Recent emails:

   [icon] #1 [sender] - [subject] ([status])
   [icon] #2 [sender] - [subject] ([status])
   ...
   ```
   Use 🔴 for high priority, 📩 for normal, ✅ for replied.

5. End with: "Say 'reply to #N' to reply, or 'check email' for new ones."
