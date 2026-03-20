# Reply to Email

## Trigger
- User says "reply to #N", "respond to #N", "reply to email N", or similar
- User says "reply to [sender name]'s email"

## Workflow

1. Identify which email the user wants to reply to. If ambiguous, ask.

2. Fetch email details:
   ```
   python -m src.tools.get_email --index N
   ```

3. Confirm with the user:
   "You want to reply to [sender]'s email about '[subject]'. What would you like to say?"

4. Wait for the user's reply instructions (they'll describe the gist casually).

5. Draft a professional reply:
   - Match the formality of the original email
   - Keep it concise but warm
   - Don't over-explain or over-apologize
   - Sign off naturally (Best, Thanks, Cheers -- match the vibe)
   - Flesh out the user's instructions into a proper email
   - Never fabricate commitments, dates, or promises the user didn't specify

6. Present the draft:
   ```
   Here's my draft reply to [sender]:

   ---
   [draft text]
   ---

   Should I send this? (yes/no, or tell me what to change)
   ```

7. If "yes" or "send it":
   - Write the draft to `/tmp/reply.txt`
   - Run:
     ```
     python -m src.tools.send_reply --gmail-id [gmail_id] --body-file /tmp/reply.txt
     ```
   - Confirm: "Reply sent to [sender]!"

8. If "no" or "cancel": "Got it, reply cancelled."

9. If the user wants edits: incorporate feedback and present a new draft (go to step 6).
