/Users/promode/Documents/AITesterBlueprin4x/chapter_08_n8n/Agents

Here is the problem statement which I want to build. I want you to build an n8n workflow that performs this: a screenshot-to-bug-reporter, where I will be uploading an image. What you will do is connect to a Git repo and create a bug report automatically in that project. 

Problem

Bug reporting is tedious and inconsistent

📥 Input:
UI Screenshot, Error Logs
↓
📤 Output:
Jira Bug with Steps to Reproduce
What it does

Analyzes a screenshot of a bug and drafts a complete bug report, including visual details.

👤 Helpful For

Testers who need to file bugs quickly without typing out every visual detail.

🔧 Implementation Guide
n8n
Webhook Trigger (image upload) → OpenAI Vision Node → Structured Output Parser → Jira Node (create issue)

put this file in the agent folder - 08_Screenshot_To_Bug_Reporter_AIAgent.json

Please lets first research which cheaper model we can use, I have access to the groq.com and openrouter io, let me know what is the plan in the Plan.md file in the agent dir of the chatper_08_n8n 

ask me for the question that you want to me anwser,

---

# How this was built

Everything below documents the build of `08_…AIAgent.json` (n8n Form Trigger) and
`09_…AIAgent_UI.json` (JSON API for the Vercel UI in `/ui_screenshotbugAIAgent`).

## 1. Decisions taken against the brief

The brief above says "connect to a Git repo" in one line and "Jira Node (create issue)"
in the implementation guide. Those are different trackers, so it was resolved explicitly:

| Question | Chosen | Why |
|---|---|---|
| Tracker | **Jira only** | Matches the implementation guide and reuses the credential already in agents 01-05 |
| Model | **Groq `qwen/qwen3.8-27b`** | Speed, and a Groq credential already existed. Not the cheapest, see section 3 |
| Intake | **n8n Form Trigger** (08), **Webhook** (09) | 08 demos without any front end; 09 serves the custom UI |
| Extras | **Attach the screenshot to the ticket** | Declined: dedup, approval gate, separate validation branch |
| UI | **Vercel + serverless proxy** | The browser must not call n8n directly, see section 5 |

## 2. The build prompt

To regenerate this from scratch in a fresh session:

> Build an n8n workflow that takes a screenshot upload plus optional error logs, sends it
> to a vision model, and files a structured bug report into Jira with the screenshot
> attached to the ticket.
>
> Constraints:
> - Do **not** use an AI Agent node. The model gets exactly one bounded job (look at the
>   image, return JSON); every other step is a deterministic node. Follow the shape of
>   agent 05, not agent 01.
> - Auth via `authentication: predefinedCredentialType` + `nodeCredentialType`. No API key
>   may appear anywhere in the exported JSON.
> - Resolve the uploaded binary as `Object.keys(item.binary)[0]` and re-key it to a stable
>   `screenshot` property. Do not hardcode the n8n-generated binary name.
> - Re-attach the binary after the HTTP call and again after the Jira create, because it
>   survives neither hop.
> - Jira description must be plain text, not wiki markup: the Cloud API wraps a plain
>   string in one ADF paragraph, so `h2.` and `{code}` would render literally.
> - Research current vision-model pricing before choosing a model. Do not assume the
>   model you remember is still served.

## 3. Model research (the non-obvious part)

Groq's vision lineup **contracted** through 2026. `llama-3.2-11b-vision-preview` was
decommissioned, and Llama 4 Scout/Maverick, which most tutorials still name as the Groq
vision option, left the supported list. The only image-capable Groq models are
`qwen/qwen3.6-27b` and `qwen/qwen3.8-27b`, both **Preview**.

| Provider | Model | $/M in | $/M out | Per report | Status |
|---|---|---|---|---|---|
| OpenRouter | `z-ai/glm-5.3-flash` | 0.075 | 0.25 | ~$0.0004 | Production |
| OpenRouter | `minimax/minimax-m3:free` | 0 | 0 | $0 | Free, ~200/day |
| **Groq (shipped)** | `qwen/qwen3.8-27b` | ~0.60 | ~3.00 | ~$0.0036 | Preview |

Groq charges a flat **2048 tokens per image**. The 5x output-over-input multiplier is the
highest on its price list, which is why the output schema is kept tight.

Lesson: **check the provider's current model list before designing around a model.**
The one you remember may not be served any more.

## 4. The prompts

Both live in the `Normalize Intake` Code node, not in the HTTP node. Multi-line strings
render readably in n8n's Code editor and collapse to one unscrollable line inside an
expression field.

### System prompt

```text
You are a senior QA engineer triaging a screenshot.

FIRST decide whether the screenshot actually shows a defect. Many screenshots show
a perfectly healthy screen. If this one does, say so: set confidence to "low" and
write a summary stating that no defect is visible. Do not manufacture a defect to
fill the schema. "Nothing is wrong here" is a correct and valuable answer.

The reporter severity guess below is only a guess. It is NOT evidence that a defect
exists and must not steer what you claim to see. Neither is the fact that someone
asked you for a report.

Only once you have decided a defect is visible, write it up.

Rules:
- Describe only what is actually visible in the image. Never invent stack traces,
  error codes, URLs, ids or user names that you cannot actually read.
- If the reporter supplied error logs, use them. Do not fabricate extra log lines.
- Quote on-screen text exactly as rendered. Never claim that text is truncated, cut
  off or clipped unless you can name the exact character it stops at.
- A screenshot being tall, wide or scaled is not a defect. Do not report cropping
  that is an artifact of how the image was captured.
- steps_to_reproduce must be concrete actions a second tester could follow. If you
  are inferring them rather than reading them, keep them short and lower confidence.
- visual_observations is where the screenshot detail belongs: layout breaks,
  overlapping elements, error banners, empty states, truncated or misaligned text,
  wrong colours, and the exact on-screen error strings you can read.
- severity is one of S1, S2, S3, S4. S1 blocks release, S4 is cosmetic.
- confidence is one of high, medium, low.

Return a single JSON object with exactly these keys:
summary, environment, steps_to_reproduce, expected_result, actual_result,
visual_observations, severity, suggested_component, confidence

summary is one line under 120 characters with no ticket prefix.
steps_to_reproduce and visual_observations are arrays of strings.
Every other value is a string.
```

### User prompt

`<<...>>` marks values interpolated from the form.

```text
Examine the attached screenshot. Decide first whether it shows a defect, then
report what you find. If nothing is wrong with it, report that.

<<'Reporter severity guess: ' + severity>>
<<'Environment: ' + environment>>

<<steps ? 'What the reporter did:\n' + steps : 'What the reporter did: not supplied.'>>

<<logs ? 'Error logs:\n' + logs : 'Error logs: none supplied.'>>
```

### Requested output schema

```json
{
  "summary": "one line, under 120 chars, no ticket prefix",
  "environment": "string",
  "steps_to_reproduce": ["array of strings"],
  "expected_result": "string",
  "actual_result": "string",
  "visual_observations": ["array of strings"],
  "severity": "S1 | S2 | S3 | S4",
  "suggested_component": "string",
  "confidence": "high | medium | low"
}
```

Enforced with Groq's `response_format: { "type": "json_object" }`, which works alongside
images. That is why no separate schema-validation branch was needed. OpenRouter's GLM 5.3
Flash accepts `response_format` but does **not** enforce a schema server-side, so swapping
to it means adding an IF node after `Parse Bug Report`.

## 5. Architecture

```
08 (form):    Form Trigger ─┐
                            ├─ Normalize Intake → Screenshot to Base64 → Groq Vision
09 (API):     Webhook ──────┘                                                │
                                                                             ▼
              Respond to UI ← Jira: Attach ← Prepare Attachment ← Jira: Create ← Parse
```

The UI never talks to n8n directly:

```
browser ──POST /api/report──▶ Vercel function ──▶ n8n webhook
(same origin, no CORS)        (N8N_WEBHOOK_URL,    Groq → Jira → respond
                               server-side only)
```

Three things that are easy to get wrong:

1. **The binary is re-attached twice.** It survives neither the HTTP hop nor the Jira
   create response. Forgetting this files a ticket with no attachment and no error.
2. **The binary key is resolved by position.** The Form Trigger and the Webhook node name
   it differently, and the naming has changed across n8n versions.
3. **`extractFromFile`'s base64 operation key is `binaryToPropery`** — a long-standing
   typo in n8n. If the node loads blank, re-pick the operation from the dropdown.

## 6. The failure that mattered

First live run through the UI: submitted a screenshot of a **healthy** page. The model
returned `"confidence": "high"` and invented a layout defect, claiming the heading was
truncated to "File a bug from a screens". None of that was in the image. Ticket VWO-126.

Two causes, both in the prompt:

- **The task framing presupposed a bug.** "Analyze the attached screenshot and *draft the
  bug report*" tells the model a bug exists. The "do not invent" rule was bullet four in a
  list and the framing beat it.
- **The severity hint primed it.** `Severity = S4 - cosmetic` was passed in, and the model
  found a cosmetic layout issue.

The fix, now in both files:

- Reframed the opening so the **first instruction is to decide whether a defect exists at
  all**, with "Nothing is wrong here" named as a correct answer.
- Told the model explicitly that the reporter's severity guess is not evidence, and
  neither is being asked for a report.
- Added a rule forbidding truncation claims unless it can name the character text stops at,
  and a rule that capture artifacts are not defects.

**The general lesson: a generator asked for X will produce X.** If "nothing to report" is a
valid outcome, the prompt has to make that an explicit first-class branch, not a caveat.

The negative case (upload a screenshot of a perfectly normal page, expect low confidence)
is therefore the **first** test to run after any prompt or model change, not the last.

## 7. Rebuild and verify

Both JSON files are generated, not hand-edited. Prompt changes go in the generator and the
file is rebuilt, so the two cannot drift.

```bash
# syntax-check every Code node before importing
python3 - <<'EOF'
import json, subprocess, tempfile, os
for p in ['08_Screenshot_To_Bug_Reporter_AIAgent.json',
          '09_Screenshot_To_Bug_Reporter_AIAgent_UI.json']:
    for n in json.load(open(p))['nodes']:
        c = n.get('parameters', {}).get('jsCode')
        if not c: continue
        t = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False)
        t.write('(function(){\n' + c + '\n});'); t.close()
        r = subprocess.run(['node', '--check', t.name], capture_output=True)
        os.unlink(t.name)
        print('OK ' if not r.returncode else 'FAIL', p[:2], n['name'])
EOF

# no embedded secrets
grep -nEi 'gsk_[A-Za-z0-9]{10,}|AIza[0-9A-Za-z_-]{30,}' 0[89]_Screenshot*.json
```

Then, in order:

1. Import, attach the Groq and Jira credentials, set `JIRA_BASE_URL` at the top of
   `Normalize Intake`, and **Activate**. An inactive workflow returns 404.
2. **Negative case first.** Upload a healthy page. Expect low confidence and an honest
   "no defect visible" summary.
3. Positive case. Upload a genuinely broken page. Expect real steps and real observations.
4. Check the ticket: the screenshot should be attached and openable.
