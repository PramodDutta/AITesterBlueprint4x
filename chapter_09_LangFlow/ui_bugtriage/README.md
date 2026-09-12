# Bug Triage UI — LangFlow

Light-mode React chat UI for the `AI4X_004_Bug_Triage_AI_Agent_Via_UI` LangFlow flow.
Type a Jira key, hit Run, get the triage rendered as markdown (tables included).

```bash
npm install
npm run dev          # http://localhost:5180
```

Config lives in `.env.local` (git-ignored, copy from `.env.example`):

```
LANGFLOW_URL=http://localhost:7860
LANGFLOW_FLOW_ID=86b832e3-7744-45a1-8130-b4e99a26c8e4
LANGFLOW_API_KEY=sk-...
```

## The call

```json
POST /api/v1/run/<flow-id>?stream=false
{
  "output_type": "chat",
  "input_type":  "chat",
  "input_value": "VWO-51",
  "session_id":  "ui-xxxx"
}
```

**`input_type` must be `"chat"`.** The flow's entry node is a ChatInput; `"text"` targets
a TextInput that does not exist here, so the key never reaches the URL template, Jira gets
`GET /rest/api/3/issue/` with an empty key, returns **405**, and the model triages the
*error response* as if it were a bug. It looks like a working run — 200 OK, a confident
report — which is what makes it dangerous. Tell the two apart by input tokens: ~150 means
it read a 405, ~2200 means it read a real ticket.

**There is no `issue_key` field.** LangFlow ignores unknown top-level keys. The ticket goes
in `input_value`.

## Why the vite proxy

The browser posts to `/api/run` on the dev server, which rewrites to the LangFlow endpoint
and injects `x-api-key`. That avoids CORS and keeps the key out of client-side JS.
See `vite.config.js`.

## Flow shape

```
ChatInput ─► Prompt Template (URL: .../issue/{issue_key})
              └─► APIRequest ─► Parser ─► Prompt Template (triage) ─► DeepSeek ─► ChatOutput
```

Note the `APIRequest` node stores a Jira `Authorization: Basic` header. Strip it before
exporting the flow JSON to a public repo — base64 is encoding, not encryption.
