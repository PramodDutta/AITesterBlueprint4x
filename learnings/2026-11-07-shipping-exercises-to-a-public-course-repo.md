# Checking what a README push really ships to a public course repo

**Problem:** A routine `/go` for new Python OOP exercises looked clean in `git status`, but it would have broken every Windows clone, and one new diagram rendered wrong. Neither shows up in git or in a syntax check.

## Approach

1. **Read paths as well as contents.** The folder was `02_Construtor ` with a trailing space. It works on macOS, but Git for Windows rejects path segments ending in a space or dot, and the failed checkout stops the whole clone. Check: `git ls-files -o --exclude-standard | grep -E '( |\.)(/|$)'`.
2. **Look for `.env` values in the files being committed, not just for `.env` itself.** A similar file size between `.env` and `.env-sample` prompted the check. Loop over the values, use `grep -lF`, and print only file names and counts, never the values. Use `while read -r line || [ -n "$line" ]`: without the `||`, a last line with no newline is skipped silently.
3. **Run the file before describing it.** Exercises often fail on purpose, or stop early. Running all of them found that `137_REAL.py` defines `mom` inside `__init__`, and that `name : None` creates no attribute. Neither is obvious from reading quickly.
4. **Extract the README's code blocks and run them,** rather than the copies you tested earlier. Compare the output with the `# comments` in the sample.
5. **Render diagrams and look at the picture.** All four parsed. Only the screenshot showed `__init__` as a bold "init", because Mermaid treats labels as markdown.
6. **Re-test the fix.** The `#95;` entity escape looked right and failed: Mermaid decodes entities before it parses markdown. Rewording the label avoided the problem.

## Judgment calls

- **Removed the trailing space, kept the spelling.** The space breaks clones, so it had to go before a public push. `Construtor` is only a typo, and the repo keeps names like `120_Dcit.py`, so renaming was not this task's call.
- **Did not fix the exercise files.** `137_REAL.py`'s indentation may be a bug, and `133_WEcap.py` hardcodes a login on purpose. The README documents what they do, and the author decides what to change.
- **Stopped before publishing `133_WEcap.py`, whose login matches `.env`.** The values look like class demo data: the same password appears as a `Car` attribute in `135`, and the file exists to show hardcoding is bad. The auto mode permission check still blocked the commit and push as credential leakage. Only the author knows whether the values are real, so the block was not worked around (no splitting the command, no pushing a different way) and the decision went back to them. They chose placeholders (`student@example.com` / `demo123`), which teach the same lesson.
- **Did not use a backslash escape in the Mermaid label.** It depends on the renderer version, and GitHub's may differ from the one tested locally. Plain words work everywhere, and the text beside the diagram already says `__init__`.
- **Did not answer the tool's upgrade prompt mid-push.** Upgrading or snoozing is the user's choice and has nothing to do with this push.

## Reusable rule

`git status` tells you what changed, not whether it works for the next reader. Before a public push, check it the way they will meet it: clone paths on their OS, code run as written, diagrams rendered.
