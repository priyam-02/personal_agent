# Skill: Reply to Email

## Trigger

User says anything like:
- "reply to #3"
- "respond to that email"
- "reply to Sarah's email"
- "reply to the one about the budget"
- "tell her I'll be there" (implies reply to most recently discussed email)

## Workflow

### Step 1: Identify the email

| User says | Action |
|-----------|--------|
| "#N" or "email N" | `python -m src.tools.get_email --index N` |
| "that email", "the last one" | `python -m src.tools.resolve_email --query "that email"` |
| "from Sarah", "about the budget" | `python -m src.tools.resolve_email --query "[their words]"` |
| Ambiguous | Ask: "Which email do you mean? Say a number or describe it." |

If the tool returns `{"error": ...}`:
- Say: "Couldn't find that email. Try 'list emails' to see what's available."
- Do NOT guess or fabricate an email.

If the tool returns `{"candidates": [...]}`:
- List the options with numbers and ask the user to pick.
- Do NOT pick one yourself.

### Step 2: Get reply instructions

If the user already gave instructions in their trigger message (e.g., "reply to #3 and say I'll be there"), skip to Step 3.

Otherwise, confirm and ask:
"Replying to [sender]'s email about '[subject]'. What should I say?"

Then STOP and wait for the user's response.

### Step 3: Draft the reply

Using the user's instructions:
1. Draft a reply following the drafting rules from the system prompt
2. Write the text to `/tmp/reply.txt`
3. Call: `python -m src.tools.stage_reply --gmail-id [gmail_id] --body-file /tmp/reply.txt`

If `stage_reply` returns an error:
- "not found": "That email isn't in my records anymore. Try 'check email' to refresh."
- "Body file" error: Re-create `/tmp/reply.txt` and retry once. If still fails: "Something went wrong. Try again?"
- Other: Report plainly.

### Step 4: Show draft and ask for confirmation

```
Draft reply to [sender]:

---
[full draft text]
---

Send this? (yes / no / tell me what to change)
```

### Step 5: ⚠️ STOP — MANDATORY ⚠️

**End your turn. Do NOT call any more tools. Do NOT call confirm_send. Wait for the user's next message.**

### Step 6: Handle user response

| User says | Action |
|-----------|--------|
| "yes", "send it", "go ahead", "looks good", "lgtm", "👍" | Call `python -m src.tools.confirm_send --confirm-token [token]` |
| "no", "cancel", "nah", "nevermind" | Say: "Cancelled." |
| "I guess", "maybe", "sure?" (ambiguous) | Ask: "Just to be safe — should I send it? Yes or no." |
| Requests changes ("shorter", "add that I'll call Monday") | Go back to Step 3 with revised draft |

After successful send: "Sent to [sender_name]."
After send error: "Reply failed: [brief reason]. Want me to try again?"

## Example: Normal Flow

```
User: "reply to #4"

Jarvis: [calls get_email --index 4]
"Replying to Lisa Park's email about 'Contract review needed'. What should I say?"

User: "tell her I'll review it tonight and sign by tomorrow morning"

Jarvis: [writes /tmp/reply.txt, calls stage_reply]
"Draft reply to Lisa:

---
Hi Lisa,

I'll review the contract tonight and have it signed by tomorrow morning.

Best,
Priyam
---

Send this?"

User: "yes"

Jarvis: [calls confirm_send]
"Sent to Lisa Park."
```

## Example: Instructions Upfront

```
User: "reply to sarah's email and say thanks for the update"

Jarvis: [calls resolve_email] [writes draft, calls stage_reply]
"Draft reply to Sarah Chen:

---
Hi Sarah,

Thanks for the update — really helpful.

Best,
Priyam
---

Send this?"

User: "make it warmer"

Jarvis: [revises, calls stage_reply again with new token]
"Updated draft:

---
Hi Sarah,

Thanks so much for the update — super helpful to have it all in one place. Appreciate you pulling it together.

Best,
Priyam
---

Send this?"

User: "yes"

Jarvis: [calls confirm_send]
"Sent to Sarah Chen."
```

## Example: Ambiguous Reference

```
User: "reply to the email about the project"

Jarvis: [calls resolve_email --query "about the project"]
"Found a few matches:
1. Lisa Park — Project Kickoff Meeting
2. Dev Team — Project Sprint Retrospective
Which one?"

User: "1"

Jarvis: [calls get_email for Lisa's email]
"Replying to Lisa Park's email about 'Project Kickoff Meeting'. What should I say?"
```

## What NOT to Do

- NEVER call `confirm_send` without explicit user approval in a separate message
- NEVER fabricate a gmail_id — always get it from a tool
- NEVER add commitments the user didn't mention
- NEVER send on ambiguous approval ("I guess", "maybe") — ask again
- NEVER skip showing the draft — even if the user seems impatient
