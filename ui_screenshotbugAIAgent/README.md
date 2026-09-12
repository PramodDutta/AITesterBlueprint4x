# Screenshot to Bug Reporter — UI

Light-mode front end for **workflow 09** (`chapter_08_n8n/Agents/09_Screenshot_To_Bug_Reporter_AIAgent_UI.json`).

Upload a screenshot, the workflow drafts a bug report from what is actually visible in
the image, files it in Jira, attaches the screenshot, and hands the ticket back here.

## Architecture

```
browser  ──POST /api/report──▶  Vercel function  ──▶  n8n webhook
(same origin, no CORS)          (N8N_WEBHOOK_URL,      Groq vision → Jira create
                                 server-side only)      → attach → Respond to UI
```

The browser never talks to n8n. That removes the CORS problem entirely and keeps the
webhook URL out of client-side code, where anyone could read it in devtools and POST to
it directly.

## Setup

**1. Deploy the workflow.** Import `09_Screenshot_To_Bug_Reporter_AIAgent_UI.json` into
n8n, attach the Groq and Jira credentials, and **Activate** it. An inactive workflow
returns 404, and a *test* webhook URL only listens while you are clicking "Test step".

**2. Edit the Jira base URL.** Open the `Normalize Intake` node and change the first line:

```js
const JIRA_BASE_URL = 'https://YOUR-DOMAIN.atlassian.net';
```

This builds the ticket link the UI shows. Everything else works without it; only the
link would be wrong.

**3. Point the UI at n8n.** In the Vercel project, **Settings → Environment Variables**:

| Name | Value |
|---|---|
| `N8N_WEBHOOK_URL` | `https://ai4xbatch.app.n8n.cloud/webhook/screenshot-bug-report` |

Already set on this project for production, preview and development. Redeploy after any
change. Until it is set, the UI shows a clear message saying so rather than failing
silently.

Note the path. The `/form/<uuid>` URL n8n shows you belongs to a **Form Trigger** and
serves n8n's own HTML page. Workflow 09 uses a **Webhook** node, so its address is
`/webhook/screenshot-bug-report`. Pointing the proxy at the form URL would file the bug
but return HTML, and the UI would report a non-JSON reply.

## Local development

```bash
npm install
npm run dev          # UI only; /api/report is not served by vite
vercel dev           # UI + the serverless function together
```

Use `vercel dev` if you want to exercise the proxy locally. Put `N8N_WEBHOOK_URL` in a
`.env.local` file (git-ignored).

## Notes

- **Paste works.** Ctrl+V a screenshot straight from the clipboard, no save-to-disk step.
- **15MB client cap.** Groq rejects a request over 20MB; the UI stops well short so the
  failure is a friendly message instead of an upstream error.
- **Low confidence is surfaced, not hidden.** When the model cannot find a defect it says
  so, and the UI shows an amber panel instead of a green one. That is the model declining
  to invent a bug, and it is the run worth demonstrating.
- **The proxy times out at 55s** and the function is configured for 60s. A slow Groq run
  plus two Jira calls can take 15-30s.

## Palette

The Testing Academy light theme.

| Token | Hex | Use |
|---|---|---|
| `paper` | `#faf9f5` | page |
| `panel` | `#f7f4ea` | inset panels |
| `edge` | `#e8e4d8` | borders |
| `ink` | `#2a2620` | body text |
| `muted` | `#6e6a5e` | secondary text |
| `clay` | `#d97757` | accent, primary button |
| `moss` | `#3f7d43` | success |
