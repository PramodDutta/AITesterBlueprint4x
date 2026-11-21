# crewai + Groq: dependency pin, stripped model prefix, running under pytest

**Problem:** `uv add crewai` failed, and once it was installed, a crewai agent on Groq returned 404 `model_not_found` and never ran under pytest.

## Approach

1. **Read the resolver's last lines first.** uv's long error ends with "your project depends on crewai and openai>=3.51.0". The project's own pin was the conflict: every crewai release needs `openai<3` (through `instructor`). Grep the repo for real `openai` SDK imports (there were none, only Groq URLs), then relax the pin to `openai>=2.30.0,<3`.
2. **Run pytest before editing.** Collection failed with a pydantic error. A module-level `Task(descritpion=...)` typo meant `description` was missing, and `agent=`/`task=` should be `agents=`/`tasks=` on `Crew`. Code at module level runs during collection, and a file without a `test_` function collects nothing. So wrap the crew in a builder function and call `kickoff()` from a `test_...` function, plus a `skipif` when `GROQ_API_KEY` is missing.
3. **Read the 404 carefully.** The request sent `gpt-oss-120b`, but `.env` had `openai/gpt-oss-120b`. Read `crewai/llm.py::_resolve_route`. A `prefix/model` string with a native prefix (`openai`) plus a custom base_url gets the prefix stripped. An explicit `provider=` keeps the model string whole.
4. **Prove it in isolation.** Make a one-line `LLM(..., provider="openai").call("Reply with just: OK")` from a scratch command, without touching the user's file. It returned OK.

## Judgment calls

- Did NOT install litellm or rename the model to `groq/...`. A one-kwarg fix in the native path is smaller, and litellm adds a big dependency.
- Did NOT rewrite the user's file a second time after they reverted it (it's a live-teaching file). Gave the diff and let them apply it.
- Did NOT add a pytest.ini or conftest. `uv run pytest <folder> -s` was enough.

## Reusable rule

When an OpenAI-compatible provider 404s on a model whose id has a slash, check whether the framework treated the first segment as a provider prefix and stripped it. Set the provider explicitly instead of renaming the model.
