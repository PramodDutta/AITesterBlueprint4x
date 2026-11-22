# Putting a CrewAI crew behind a minimal web UI

**Problem:** a CrewAI script built its tasks at import time from a hardcoded `bug_report` and a CLI `--bug-id`, so it could only triage one bug per process run and had no UI.

## Approach

1. **Make the crew reusable, don't rebuild it.** The task descriptions were f-strings (`f"""...{bug_report}..."""`), so the bug text was baked in when the module loaded. Drop the `f` so `{bug_report}` stays a literal placeholder, keep the agents, tasks and `Crew` at module level, and call `crew.kickoff(inputs={"bug_report": text})` per request. CrewAI fills `{name}` placeholders in task descriptions and agent text from `inputs`.
2. **Before doing that, grep every agent/task string for `{` and `}`.** CrewAI interpolates all of them, so a stray literal brace (JSON examples, code snippets) would break. Here there were exactly three `{bug_report}` hits, so it was safe.
3. **Fetch the input per request**, inside a `run_triage(bug_id)` function: Jira fetch, then kickoff, then join `result.tasks_output[i].raw` with agent labels into one copy-ready string.
4. **Never run the crew inside the HTTP request.** A 3-agent crew takes 1-3 minutes. `POST /api/triage` starts a `threading.Thread` and returns a `job_id` right away; the page polls `GET /api/status/<job_id>` every 1.5s and shows elapsed seconds.
5. **Serialize runs with a `threading.Lock`** around `kickoff`, because every request shares the one `Crew` object.
6. **Use the standard library for the server** (`ThreadingHTTPServer` plus an inline HTML string). Silence `log_message` so the terminal keeps CrewAI's verbose agent trace.
7. **Verify end to end through the API** (real ticket returns a full report, unknown ticket returns a clean error) before opening the browser.

## Judgment calls

- **No Flask, Streamlit or Gradio.** None were installed, and the user asked for lightweight and fast. The stdlib keeps it to zero installs and one file.
- **Didn't edit the CLI script.** The UI lives in its own file (`..._PROD_UI.py`), so the teaching version stays unchanged.
- **No live per-agent streaming.** `task_callback` could show each agent's section as it lands, but the user asked for minimal. The seconds counter plus the terminal trace was enough.
- **Didn't rebuild agents per request.** That would also work, but the `inputs` templating is the idiomatic CrewAI path and keeps the long prompts untouched (indenting them into a function would have shifted the text inside the triple-quoted strings).
- **Bound to 127.0.0.1 only.** It holds Jira and LLM keys, so it should not be exposed on the LAN by default.

## Gotcha

In zsh, `s=$(curl ...); echo "$s" | python -c 'json.load(...)'` fails with "Invalid control character", because zsh's `echo` turns the `\n` escapes inside the JSON into real newlines. The server was fine. Pipe `curl` straight into the parser, or use `printf '%s'`.

## Reusable rule

To serve a script-style CrewAI crew, turn its f-string inputs into `{placeholders}` filled by `kickoff(inputs=...)`, and run kickoff in a background job the browser polls. Never hold an HTTP request open for an LLM crew.
