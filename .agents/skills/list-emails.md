# Skill: List Emails

## Trigger

User says anything like: "list emails", "show recent emails", "what emails have I gotten?", "show my inbox", "what's in my inbox?"

## Workflow

### Step 1: Fetch email list
```
python -m src.tools.list_emails --limit 10
```

### Step 2: Handle errors

If the tool fails:
- Say: "Couldn't load the email list. Try 'check email' to refresh."

### Step 3: Handle empty results

If `emails` is empty or `total_count` is 0:
- Say: "No emails processed yet. Say 'check email' to fetch new ones."

### Step 4: Format output

Present as a compact list — one line per email, no summaries:

```
<b>Recent emails:</b>

[icon] #[index] [sender] — [subject] ([status])
[icon] #[index] [sender] — [subject] ([status])
...

Reply to any: <code>reply to #N</code>
Check for new: <code>check email</code>
```

Icons:
- 🔴 = `priority: "high"`
- 📩 = `priority: "normal"`
- ✅ = `status: "replied"`

### Complete Example

User: "show my emails"

Jarvis:
```
<b>Recent emails:</b>

🔴 #4 Lisa Park — Urgent: Contract review needed (new)
📩 #5 Dev Team — Sprint retrospective notes (new)
✅ #3 Sarah Chen — Q3 Budget Review (replied)
📩 #2 Mark Johnson — Team lunch Friday? (new)
✅ #1 HR — Benefits enrollment reminder (replied)

Reply to any: <code>reply to #N</code>
Check for new: <code>check email</code>
```

### What NOT to Do

- Do NOT include email summaries — keep it to one line per email
- Do NOT add commentary ("Busy day!" or "Quiet inbox!")
- Do NOT truncate without telling the user — if there are more, say: "Showing 10 of [total]. Say 'list emails --limit 20' for more."
