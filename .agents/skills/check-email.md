# Skill: Check Email

## Trigger

User says anything like: "check my email", "any new emails?", "check inbox", "what's new?", "new messages?"

## Workflow

### Step 1: Fetch emails
```
python -m src.tools.check_email --max 10
```

### Step 2: Handle errors

If the tool fails (exception, non-JSON output, or stderr):
- Say: "Couldn't reach Gmail right now. Try again in a minute — if it keeps failing, the auth might need a refresh."
- Do NOT retry automatically.

### Step 3: Handle empty results

If `new_emails` is an empty array:
- Say: "No new important emails since last check."
- Do NOT explain the process or add filler.

### Step 4: Summarize each email

For each object in `new_emails`:
1. Read the `body_text` field (this is the full email body — YOU summarize it)
2. Apply the summarization rules from the system prompt
3. Do NOT call any external API — you are the summarizer

### Step 5: Format output

Present each email using this template:

```
[icon] <b>Email #[index]</b>
From: [sender]
Subject: [subject]

[your 2-3 sentence summary]

→ Reply: <code>reply to #[index]</code>
```

Use 🔴 for `priority: "high"`, 📩 for `priority: "normal"`.

After all emails:
"[N] new email(s). [skipped_count] filtered as noise."

### Complete Example

User: "check my email"

Jarvis:
```
🔴 <b>Email #4</b>
From: Lisa Park
Subject: Urgent: Contract review needed

She needs you to review the vendor contract and sign by EOD Wednesday. Contract value is $120K — legal has approved their side.

→ Reply: <code>reply to #4</code>

📩 <b>Email #5</b>
From: Dev Team
Subject: Sprint retrospective notes

FYI only — no action needed. Velocity was up 15% last sprint, two bugs carried over.

→ Reply: <code>reply to #5</code>

2 new email(s). 4 filtered as noise.
```

### What NOT to Do

- Do NOT call any external API or LLM to summarize — you ARE the summarizer
- Do NOT include email signatures or footers in summaries
- Do NOT say "Let me check your email for you" before running the tool
- Do NOT list skipped/filtered emails — just mention the count
- Do NOT add commentary ("Busy day!" or "Looks quiet")
