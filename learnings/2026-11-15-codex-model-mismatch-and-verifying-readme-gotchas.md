# Codex model mismatch, and verifying README gotchas before shipping

**Problem:** `codex-image.sh` exited 4 with `model_not_found`. `~/.codex/config.toml` pins `gpt-6.1-sol`, and a ChatGPT login doesn't accept that model. Separately, a README "gotcha" I wrote from memory turned out to be false.

## Approach

1. Read the actual error text instead of retrying blind. `model_not_found` + "not supported when using Codex with a ChatGPT account" means a config problem, not a network one.
2. Ran `codex-image.sh --help` and saw a `--model` flag that overrides the config for one run.
3. Found the models the account can really use in `~/.codex/models_cache.json` (its `models[].slug` list): `gpt-6-sol`, `gpt-6-astra`, `gpt-6-luna`, `gpt-5.6-*`.
4. Re-rendered with `--model gpt-6-sol`. It worked first time and I used it for all four images.
5. QA'd every render by zooming in on small labels (`sips -c` crop + `sips -z` upscale). One render had a malformed "m" in `util_module.py`. I spelled the word letter by letter in the brief and asked for the "m" to be drawn clearly in every place it appears. The second render was clean.
6. Before committing the README, ran each claim it makes: script outputs, the pytest summary, and the gotchas. The claim "run `177_Util.py` from another folder and the import fails" was false. Python puts the **script's folder** on `sys.path`, not the current folder. The real failure is the same import in a script under a sibling folder (`12_PyTest/`). I rewrote the bullet to say that, and checked it.

## Judgment calls

- **Did not edit `~/.codex/config.toml`.** It's the user's global config and other tools may rely on that pin. A per-run `--model` fixes the task without side effects. The user should hear about it, though.
- **Did not change the user's exercise files** (`167_Fix2py` has no `.py`; `174_OS.py` removes `AI.txt` and then renames the same file). They're class material, so I reported them instead of fixing them.
- **Did not trust a crop-free read of the image.** At full size the bad "m" looked almost fine. The zoomed crop showed it.
- **Added `.venv/` and `.pytest_cache/` to `.gitignore`** even though uv's inner `.gitignore` already hides them. That way a later `git add -A` can't sweep them in.

## Reusable rule

When a tool fails on its model or config, read the error, look for a per-run override flag and the tool's local cache of valid values, and never edit the user's global config to get past it. And run every "gotcha" in a README before shipping it, because the plausible-sounding ones are the ones that are wrong.
