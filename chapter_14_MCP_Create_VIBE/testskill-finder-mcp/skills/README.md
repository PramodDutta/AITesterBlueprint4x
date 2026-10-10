# QA Skill Suite — organized by STLC

36 Agent Skills for the full **Software Testing Life Cycle**, by TheTestingAcademy.
Folders are **numbered in STLC order** so you read them the way testing actually flows:
requirement → plan → design → cases → execute → defects → closure.

Each skill is a folder with a `SKILL.md` (YAML frontmatter + instructions). Drop any
folder into `~/.claude/skills/` for Claude Code, or convert its body to a
`.github/prompts/*.prompt.md` for GitHub Copilot.

## The 7 STLC phases (14 skills)

| Phase | Folder | Skills |
|-------|--------|--------|
| 1 · Requirement Analysis | `01-requirement-analysis/` | `jira-requirement-analyzer` |
| 2 · Test Planning | `02-test-planning/` | `test-plan-generator` ⭐ |
| 3 · Test Design | `03-test-design/` | `test-scenario-designer`, `api-test-designer` |
| 4 · Test Case Development | `04-test-case-development/` | `test-case-writer`, `test-data-generator` |
| 5 · Test Execution | `05-test-execution/` | `automation-script-generator`, `test-execution-tracker`, `regression-suite-selector` |
| 6 · Defect Management | `06-defect-management/` | `bug-reporter`, `bug-triage-assistant`, `rca-analyzer` |
| 7 · Test Closure | `07-test-closure/` | `test-coverage-analyzer`, `test-closure-reporter` |

⭐ `test-plan-generator` is the fully-worked example — it ships with `references/`
(checklist + template), `scripts/fetch_jira.sh`, and a Copilot `prompt.md`.

## Framework packs (22 skills — cross-cutting automation)

| Pack | Folder | Stack |
|------|--------|-------|
| Playwright | `framework-packs/playwright-pack/` | TypeScript · `getByTestId`/web-first · 11 skills |
| Selenium | `framework-packs/selenium-pack/` | Java · Selenium 4 + TestNG · 11 skills |

## The flow — skills hand off to each other

```
01 analyze ticket ─▶ 02 plan ─▶ 03 design scenarios ─▶ 04 write cases + data
                                                              │
   07 closure ◀─ 06 defects ◀─ 05 execute (Playwright / Selenium pack) ◀┘
```
Every skill stops at a **human-review gate** and never fabricates data.

## Install

```bash
# one skill
cp -r ./02-test-planning/test-plan-generator ~/.claude/skills/

# a whole phase
cp -r ./05-test-execution/* ~/.claude/skills/

# a framework pack
cp -r ./framework-packs/playwright-pack/* ~/.claude/skills/
```

See the masterclass (`../index.html`) for the full walkthrough.
