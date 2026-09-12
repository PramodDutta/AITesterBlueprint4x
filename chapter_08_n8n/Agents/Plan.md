# Plan: 08 Screenshot to Bug Reporter

Design notes and model research for `08_Screenshot_To_Bug_Reporter_AIAgent.json`.

## The problem

Bug reporting is tedious and inconsistent. A tester sees a broken screen, grabs a
screenshot, then retypes every visual detail into a ticket by hand. The detail that
matters most (the red banner, the overlapping div, the truncated error string) is exactly
the part people summarise away.

```
Input:   UI screenshot + error logs
Output:  Jira bug with steps to reproduce, and the screenshot attached
```

## Model research

The interesting finding, and the reason this file exists.

**Groq's vision lineup contracted through 2026.** `llama-3.2-11b-vision-preview` was
decommissioned. Llama 4 Scout and Maverick, which most 2026 tutorials still name as the
Groq vision option, no longer appear on the supported model list. As of September 2026
Groq's only image-capable models are `qwen/qwen3.6-27b` and `qwen/qwen3.8-27b`, and both
carry **Preview** status, which Groq defines as evaluation rather than production.

| Provider | Model | $/M in | $/M out | Per report | Status |
|---|---|---|---|---|---|
| OpenRouter | `z-ai/glm-5.3-flash` | 0.075 | 0.25 | ~$0.0004 | Production |
| OpenRouter | `minimax/minimax-m3:free` | 0 | 0 | $0 | Free, ~200/day |
| **Groq (shipped)** | `qwen/qwen3.6-27b` | 0.60 | 3.00 | ~$0.0036 | Preview |

Cost basis for the shipped model: Groq charges a flat **2048 tokens per image**, plus
roughly 500 prompt tokens at $0.60/M, plus roughly 700 output tokens at $3.00/M. That is
about **275 bug reports per dollar**.

Groq's 5x output-over-input multiplier on this model is the highest on its price list, so
the output schema is deliberately tight. Every field the model returns is one it has to
pay for.

Groq vision limits, confirmed: 20MB max request, 5 images max for qwen3.6 (3 for
qwen3.8), and both JSON mode and tool use work alongside images.

### Why Groq, given it is the expensive option here

Speed, and the fact that a Groq credential already exists in this n8n instance. The
tradeoff is accepted knowingly. Two mitigations are built in:

1. The model id appears in exactly **one place** (the `jsonBody` of the Groq node), so
   swapping it when Groq rotates models again is a one-field edit.
2. Groq supports `response_format: {"type": "json_object"}` **with** images, so JSON mode
   carries the structure. This is what let the workflow skip a separate schema-validation
   branch. GLM 5.3 Flash would have needed one, since it accepts `response_format` but
   does not enforce a JSON schema server-side.

### Switching to OpenRouter

Change three things in the `Groq Vision - Draft Bug Report` node:

| Field | Groq | OpenRouter |
|---|---|---|
| `url` | `https://api.groq.com/openai/v1/chat/completions` | `https://openrouter.ai/api/v1/chat/completions` |
| `nodeCredentialType` | `groqApi` | `openRouterApi` |
| `model` in `jsonBody` | `qwen/qwen3.6-27b` | `z-ai/glm-5.3-flash` |

Both APIs are OpenAI-compatible, so the messages array and the base64 `image_url` shape
are identical. If you move to GLM, add an IF node after `Parse Bug Report` to catch
schema drift.

## Architecture

```
Form Trigger -> Normalize Intake -> Screenshot to Base64 -> Groq Vision (HTTP)
                                                                  |
                     Jira: Create Bug <- Parse Bug Report <-------+
                             |
                     Prepare Attachment -> Jira: Add Attachment
```

This is **not** an AI Agent node. The model gets exactly one bounded job (look at the
image, return JSON) and every other step is a deterministic node. That is the agent-05
shape, not the agent-01 shape. An agent node would also make the image path harder to
control, since the tool-calling loop decides when and whether to look.

### Nodes

| # | Node | Type | Job |
|---|---|---|---|
| 1 | On bug report submission | `formTrigger` 2.2 | Hosted upload page: screenshot (required), error logs, steps, severity, environment |
| 2 | Normalize Intake | `code` 2 | Resolve the binary, build the system and user prompts |
| 3 | Screenshot to Base64 | `extractFromFile` 1.1 | Binary to a base64 string in `screenshot_b64` |
| 4 | Groq Vision - Draft Bug Report | `httpRequest` 4.5 | One vision call, JSON mode, temp 0.1 |
| 5 | Parse Bug Report | `code` 2 | Parse the response, render the Jira description, re-attach the binary |
| 6 | Jira - Create Bug | `jira` 1 | VWO project (10033), Bug type (10042) |
| 7 | Prepare Attachment | `code` 2 | Carry the issue key and the binary forward |
| 8 | Jira - Attach Screenshot | `jira` 1 | `issueAttachment` / `add` |

Plus three sticky notes.

### Three decisions worth knowing

**The binary property is resolved by position, not by name.** The Form Trigger names the
uploaded binary after the field label, and the exact form has changed between n8n
versions. Node 2 takes `Object.keys(item.binary)[0]` and re-keys it to a stable
`screenshot` property. Everything downstream depends on that name instead of on n8n's.

**The binary is re-attached twice.** Binary data does not survive the HTTP hop, and Jira's
create response carries none either. Node 5 pulls it back from
`$('Normalize Intake').first().binary`, and node 7 does the same, so the attachment step
still has the PNG.

**The prompts live in the Code node, not the HTTP node.** Multi-line strings render
readably in n8n's Code editor and become one unscrollable line inside an expression field.
The tradeoff is that the prompt sits one node upstream of the call that uses it.

**The description is plain text, not Jira wiki markup.** The Cloud API wraps a plain
string in a single ADF paragraph, so `h2.` and `{code}` would render literally.

### No secrets in this file

Agent 07 shipped a raw `x-goog-api-key` header and had to be redacted before commit. This
one authenticates by reference:

```json
"authentication": "predefinedCredentialType",
"nodeCredentialType": "groqApi"
```

The same mechanism agent 05 uses for its Jira REST calls. Nothing to redact, nothing to
rotate.

## Setup

1. Import via **Workflows > Import from File**.
2. Confirm both credentials attached: **Groq account** on node 4, **Jira SW Cloud
   account** on nodes 6 and 8.
3. Check node 3 shows the operation **Move File to Base64 String**. The internal key is
   `binaryToPropery`, an old n8n typo. If the node loads blank, re-pick the operation from
   the dropdown.
4. Change the Jira project and issue type if you are not filing into VWO. Current values
   are project `10033` and issue type `10042`.
5. Activate, then open the form URL from the trigger node.

## Verification

Automated checks that already pass on the committed file:

- Valid JSON; every `connections` key and target resolves to a real node name
- Node ids unique and UUID4-shaped; all positions multiples of 16
- Only the two known credential ids appear
- No embedded API key matches (`gsk_`, `Bearer`, `AIza`, `AQ.`)
- The chain is linear, 8 nodes, ending at the attachment step

Manual runs, in this order:

1. **Happy path.** Upload a screenshot of a genuinely broken page plus a few log lines.
   Expect a VWO bug with numbered steps and the PNG attached and openable.
2. **Response shape.** Open node 4's output. `choices[0].message.content` should be bare
   JSON, not prose and not a fenced block. Node 5 strips one fence if it appears, but a
   fence every time means the prompt needs tightening.
3. **The negative case, which is the one worth showing in class.** Upload a screenshot of
   a perfectly normal page. A good run returns `confidence: low` and an honest summary. A
   bad run invents a defect to fill the schema. This is the run that tells you whether the
   system prompt's "do not invent" rules are actually holding.

## Known risks

- **The model is Preview.** Groq has already retired one vision line. Expect to swap the
  model id; the table above has the fallbacks.
- **Form binary naming** is the least certain part of the file, which is why node 2
  resolves it dynamically rather than hardcoding.
- **Text-heavy screenshots.** The 2048-token image charge is flat regardless of
  resolution, so a very dense screenshot costs the same as a sparse one but may exceed
  useful legibility. A downscale or crop step is a possible later addition.
