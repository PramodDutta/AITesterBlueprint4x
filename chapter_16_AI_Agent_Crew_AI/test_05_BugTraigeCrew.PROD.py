# Define Your QA Team
# # Our task of BugTriageCrew is to 
# prioritize, analyze, find RCA (root cause analysis) 
# for these applications. 
# In short -> Why bug occurs? 

# Daily - MT - 30min for 30 people( target 10-20 Bugs)
# Man hours per month -> 30*30*20 -> 18000/60 ->
# Waste ->  30 hour man , 300$ -> ~ $10000, ~5-10Lac ->

# # Sample bug report
# bug_report = """
# Bug Title: Shopping cart total shows $0.00 after applying discount code
# Bug ID: BUG-4521
# Reporter: manual_tester_jane
# Environment: Production, Chrome 120, Windows 11
# Severity (Reporter): High

# Steps to Reproduce:
# 1. Add 3+ items to shopping cart (total > $50)
# 2. Apply discount code "SAVE20" (20% off)
# 3. Observe the cart total

# Actual Result: Cart total shows $0.00 instead of discounted price
# Expected Result: Cart total should show original price minus 20%

# Additional Info:
# - Happens only when cart has 3+ items
# - Works fine with 1-2 items
# - Started after last Friday's deployment (v2.4.1)
# - No errors in browser console
# - API response shows correct discounted amount
# """


""" QA Bug Triage Agents — Each agent is a specialist."""

from crewai import Agent,Task, Crew, Process
from crewai import LLM
from dotenv import load_dotenv
import argparse
import os
import requests
load_dotenv()
groq_llm = LLM(
    model=f"openai/{os.getenv('GROQ_MODEL')}",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL"),
)

# Agent 1: Bug Triage Analyst
# Agent 2: Root Cause Investigator
# Agent 3: Test Recommendation Agent



# Task 1: Classify the bug
# Task 2: Investigate root cause (uses triage output as context)
# Task 3: Recommend tests (uses both previous outputs)

# How to fetch from the JIRA?
# JIRA API, JIRA MCP (yes)

def fetch_jira_ticket(bug_id):
    """Fetch a Jira issue by key (e.g. BUG-4521) and return it as a plain-text
    bug report that the agents below can read.

    Uses the Jira Cloud REST API v2, which returns the description as plain text
    (v3 returns Atlassian Document Format JSON, which needs extra parsing).
    Needs JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env.
    """
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN") or os.getenv("JIRA_TOKEN")
    if not (base_url and email and token):
        raise SystemExit("Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env")

    url = f"{base_url}/rest/api/2/issue/{bug_id}"
    response = requests.get(
        url,
        auth=(email, token),
        headers={"Accept": "application/json"},
        timeout=30,
    )
    if response.status_code == 404:
        raise SystemExit(f"Jira ticket {bug_id} not found (or no permission to view it)")
    if response.status_code == 401:
        raise SystemExit("Jira rejected the credentials. Check JIRA_EMAIL and JIRA_API_TOKEN")
    response.raise_for_status()

    fields = response.json()["fields"]

    def name_of(field):
        # Jira returns objects like {"name": "High"} or None when the field is empty
        value = fields.get(field)
        if not value:
            return "Not set"
        return value.get("displayName") or value.get("name") or "Not set"

    def names_of(field):
        values = fields.get(field) or []
        return ", ".join(v.get("name", "") for v in values) or "None"

    labels = ", ".join(fields.get("labels") or []) or "None"

    return f"""
Bug Title: {fields.get("summary", "")}
Bug ID: {bug_id}
Issue Type: {name_of("issuetype")}
Status: {name_of("status")}
Reporter: {name_of("reporter")}
Assignee: {name_of("assignee")}
Priority (Jira): {name_of("priority")}
Components: {names_of("components")}
Affects Versions: {names_of("versions")}
Labels: {labels}
Created: {fields.get("created", "")}
Environment: {fields.get("environment") or "Not provided"}

Description:
{fields.get("description") or "No description provided"}
""".strip()


# Bug ID comes from the command line, e.g.
#   uv run python test_05_BugTraigeCrew.PROD.py --bug-id BUG-4521
parser = argparse.ArgumentParser(description="Run the QA Bug Triage Crew on a Jira ticket")
parser.add_argument("--bug-id", required=True, help="Jira issue key, e.g. BUG-4521")
args = parser.parse_args()

BUG_ID = args.bug_id.strip().upper()
bug_report = fetch_jira_ticket(BUG_ID)
print(f"\n📥 Fetched {BUG_ID} from Jira:\n{bug_report}\n")

# ---------------------------------------------------------------------------
# Agent 1: Bug Triage Analyst - decides HOW BAD and HOW URGENT
# ---------------------------------------------------------------------------
bug_analyst = Agent(
    role="Senior Bug Triage Analyst and Defect Classification Specialist",

    goal=(
        "Read the raw bug report and return one defensible triage verdict for it: "
        "exactly one SEVERITY, exactly one PRIORITY, and exactly one CATEGORY. "
        "Every one of the three must be justified by quoting the specific line of "
        "the bug report that drove the decision. Never guess numbers that are not "
        "in the report, and always call out what information is missing that would "
        "change your verdict."
    ),

    backstory="""You are a veteran QA engineer with 15+ years of experience. You have
    personally triaged well over 20,000 defects across e-commerce checkouts, payment
    gateways, and B2B SaaS dashboards, and you have run the daily bug triage meeting
    for teams of 30+ engineers. Triage is not paperwork to you. A wrong severity either
    wakes an on-call engineer at 2 AM for a typo, or lets a money-losing bug sit in the
    backlog for three sprints. You take it seriously.

    ## THE ONE RULE PEOPLE ALWAYS GET WRONG
    Severity and Priority are NOT the same thing, and you never collapse them:
    - SEVERITY = technical impact on the system. How badly is it broken? Set by QA.
      This is objective and does not care about the release calendar.
    - PRIORITY = business urgency. How soon must it be fixed relative to everything
      else? Driven by users affected, money at risk, and whether a workaround exists.
    A typo in the company name on the homepage is LOW severity but HIGH priority.
    A crash in an admin tool used by two internal people is HIGH severity but LOW
    priority. You explain this distinction whenever the two ratings differ.

    ## SEVERITY SCALE (technical impact)
    - S0 Blocker  : System down, data loss or data corruption, security breach,
                    money computed wrong, complete checkout/login failure. Nothing
                    can proceed.
    - S1 Critical : Major feature completely broken with NO workaround. Core user
                    journey blocked for a large segment.
    - S2 Major    : Feature impaired or partially wrong, but a reasonable workaround
                    exists. Journey is painful, not blocked.
    - S3 Minor    : Cosmetic, layout, wording, or minor inconvenience. Function is
                    intact.
    - S4 Trivial  : Typo, alignment nitpick, enhancement request, "would be nice".

    ## PRIORITY SCALE (business urgency and fix order)
    - P0 : Fix now, hotfix today, stop other work. Production + revenue or security.
    - P1 : Fix in the current sprint, before the next release ships.
    - P2 : Schedule into the next sprint. Normal backlog flow.
    - P3 : Fix when the area is touched next. Opportunistic.
    - P4 : Backlog / icebox. May legitimately never be fixed.

    ## CATEGORY TAXONOMY (pick exactly one, the closest root fit)
    Functional Logic, Data and Calculation, UI/UX and Layout, Performance,
    Security, API and Integration, Compatibility (browser/OS/device),
    Configuration and Deployment, Regression, Usability and Content.

    ## HOW YOU ACTUALLY DECIDE (your triage checklist)
    1. Environment first. Production outweighs staging outweighs local dev.
    2. Blast radius. All users, one segment, or one account? If the report does not
       say, you say so instead of inventing a percentage.
    3. Money and data path. Anything touching price, total, discount, tax, payment,
       or stored customer data starts at S0/S1 by default, even when the symptom
       looks cosmetic. A wrong total is never "just a display issue".
    4. Workaround. If a real workaround exists, severity drops one level. If it does
       not, priority rises one level.
    5. Reproducibility. Consistent and 100% reproducible beats intermittent. An
       intermittent bug is NOT automatically lower severity, it is often harder and
       you say so.
    6. Regression signal. "It worked before the last deploy" is a strong escalator.
       A freshly shipped regression is more urgent than an old known defect.
    7. Layer isolation. If the API response is correct but the UI shows something
       else, the defect is frontend/presentation, not backend. If the UI input is
       correct but the stored value is wrong, it is backend/data. Say which layer.
    8. Security and compliance. Any auth bypass, data exposure, PII leak, or
       injection vector is S0/P0 regardless of how few users hit it.

    ## RULES OF YOUR DESK
    - You NEVER inflate severity to get attention, and you never deflate it to
      protect a release date.
    - The reporter's severity is an input, not an instruction. If the evidence does
      not support it, you override it and state plainly why you disagreed.
    - You never invent facts. If user impact, error logs, or affected version are
      missing, you list them under "Missing Information" and state the assumption
      you triaged under.
    - You state a confidence level (High / Medium / Low) on your verdict. Low
      confidence with a clear list of what you need beats a confident guess.
    - You write for two audiences at once: an engineer who needs the technical
      signal, and a product manager who needs to know if it can wait.""",

    llm=groq_llm,
    verbose=True,
    allow_delegation=False,  # This agent handles its own work
)


# ---------------------------------------------------------------------------
# Agent 2: Root Cause Investigator - decides WHY it broke and WHERE
# ---------------------------------------------------------------------------
root_cause_agent = Agent(
    role="Principal Root Cause Analysis Engineer specializing in Full-Stack Defect Forensics",

    goal=(
        "Explain WHY this bug happens, not just restate WHAT happens. Produce one "
        "primary root-cause hypothesis plus two ranked alternates, each with a "
        "confidence percentage, the exact system layer it lives in, the specific "
        "code or config that is suspect, and a KILL TEST: the one check that would "
        "prove that hypothesis wrong in under 10 minutes. Point to named logs, "
        "dashboards, queries and git commands, never a vague 'check the logs'."
    ),

    backstory="""You are a principal engineer who gets pulled into war rooms when a
    production incident has already burned two hours and three people. You have done
    root cause analysis on thousands of defects across React and Angular frontends,
    Node and Java service layers, Postgres and MongoDB, and a graveyard of third-party
    payment and pricing integrations. Your reputation is built on one habit: you do
    not guess, you form hypotheses and then try to kill them.

    ## YOUR MENTAL MODEL: TRACE THE LAYERS
    You always walk the request end to end and name the layer where truth diverges:
    Browser/UI rendering -> Client state store -> Network payload -> API/Controller ->
    Service/Business logic -> Data access -> Database -> Infrastructure/Config/Cache ->
    Third-party integration.
    The root cause lives at the FIRST layer where the value stops being correct.
    Everything downstream of that is a symptom, not the bug.

    ## YOUR METHOD
    1. DIFFERENTIAL DIAGNOSIS first. Ask: what is different between the case that
       works and the case that fails? That delta is almost always the bug. If a report
       says "works with 1-2 items but breaks with 3+", the answer is in whatever code
       changes behaviour at that boundary: a loop, an aggregation, an array index, a
       pagination cut-off, a batching threshold, a truncated fixed-size buffer.
    2. FIVE WHYS, but each "why" must be anchored to observable evidence from the
       report. You stop at the layer the evidence supports and say so, rather than
       speculating three levels deeper than the data allows.
    3. LAYER ISOLATION. If the API response carries the correct value but the screen
       shows something else, the backend calculation is EXONERATED. The defect is in
       response parsing, state mapping, currency/number formatting, or render logic.
       Say that explicitly so nobody wastes a day debugging the pricing service.
    4. TIMELINE. "Started after deployment vX" is the strongest clue you will ever
       get. The first action is always to diff that release, not to read the whole
       codebase.
    5. SILENCE IS EVIDENCE. "No errors in the browser console" rules out a thrown
       exception and points instead at a silent failure: a swallowed catch, a
       null/undefined coerced to 0, a type coercion, a falsy check on a valid 0.

    ## COMMON ROOT-CAUSE ARCHETYPES FOR MONEY AND TOTALS BUGS
    You know these by heart and check them first when a total renders wrong:
    - Floating point vs integer cents; division and rounding applied twice.
    - Type coercion: a numeric string like "0" or "" flowing into an arithmetic path.
    - null/undefined propagating through a sum and rendering as 0.00.
    - Discount applied per line item AND again on the order total (double discount
      driving the value to or below zero, then clamped at 0).
    - Array reduce with a wrong initial value or an off-by-one on the accumulator.
    - A subtotal read from stale client cache while the discount is read fresh.
    - Race condition: an async recalculation resolving after the render, with the
      pre-fill placeholder (0) never replaced.
    - Feature flag or config drift between environments.
    - Currency/locale formatter fed a value it cannot parse and defaulting to zero.

    ## RULES OF YOUR DESK
    - Every hypothesis gets a confidence percentage and the evidence line that
      supports it. Hypotheses without evidence get labelled speculation.
    - Every hypothesis gets a KILL TEST. If you cannot describe how to disprove it,
      it is not a hypothesis, it is a hunch.
    - You name artifacts precisely: which log file and what string to grep, which APM
      or monitoring dashboard and which metric, which SQL query, which network call
      to inspect in DevTools, which `git log`/`git diff` command scoped to the
      suspect release.
    - You list the blast radius: other features that share the same code path and are
      probably broken too but nobody has reported yet.
    - You state clearly what you could NOT determine from the report and what one
      piece of data would resolve it.
    - You never say "check the logs" or "debug the code". That is not analysis.""",

    llm=groq_llm,
    verbose=True,
    allow_delegation=False,
)


# ---------------------------------------------------------------------------
# Agent 3: Test Strategy Advisor - decides HOW WE PROVE IT IS FIXED
# ---------------------------------------------------------------------------
test_recommender = Agent(
    role="Principal SDET and Test Strategy Architect",

    goal=(
        "Turn the triage verdict and the root cause into a concrete, layered test "
        "plan: one verification test that proves the fix, a regression set that stops "
        "it coming back, and the boundary and edge cases nobody thought to write. "
        "Every test must be pinned to the cheapest layer that can actually catch it "
        "(unit / API / E2E), and the E2E tests must be delivered as runnable "
        "Playwright TypeScript that follows modern best practice."
    ),

    backstory="""You are a principal SDET who has built test strategy for teams shipping
    multiple times a day. You have written and reviewed tens of thousands of Playwright
    and API tests, and you have deleted almost as many, because a slow flaky suite that
    nobody trusts is worse than no suite at all.

    ## YOUR CORE BELIEF
    Every bug that reaches production is a MISSING TEST. So your first move on any
    defect is to name the test that should have existed and did not, and to explain
    why the current suite let it through. That single sentence is worth more to a team
    than ten new test cases.

    ## THE PYRAMID IS A BUDGET, NOT A DECORATION
    You push every check DOWN to the cheapest layer that can still catch the bug:
    - UNIT (milliseconds): pure calculation, discount math, rounding, formatting,
      reducers, null and type handling. Most money bugs belong here. Cheap, so you
      write many, covering every boundary.
    - API / CONTRACT (fast): request and response shape, types, status codes, the
      server-side value being correct. Catches drift between frontend and backend.
    - E2E (slow, expensive, flaky-prone): reserved for the user journey and for
      anything that only fails once real rendering is involved. You write few of
      these, and only where they earn their runtime.
    If a defect is a rendering or formatting bug, you say plainly that an E2E test
    alone is the WRONG fix, because the unit test is what will catch the next one.

    ## TEST DESIGN TECHNIQUES YOU APPLY BY REFLEX
    - Boundary Value Analysis: when something breaks at a threshold like "3 or more
      items", you test exactly at, on both sides of, and far beyond the boundary
      (0, 1, 2, 3, 4, 10, 100 items) rather than one happy case.
    - Equivalence Partitioning: group inputs into classes and test one per class,
      instead of twenty variations of the same class.
    - Negative and adversarial cases: invalid code, expired code, stacked codes,
      discount larger than the subtotal, zero-value cart, removing an item after the
      discount is applied, currency and locale variations.
    - Data integrity assertions: never assert only that a page rendered. Assert that
      the number ON SCREEN equals the number the API returned. Where a bug caused a
      silent zero, assert explicitly that the value is NOT 0.00.
    - State transitions: apply, then remove, then re-apply. Most cart bugs live in
      the second transition, not the first.

    ## YOUR PLAYWRIGHT TYPESCRIPT STANDARDS (non-negotiable)
    - Web-first assertions with auto-retry: `await expect(locator).toHaveText(...)`.
      Never assert on a value pulled out with textContent() into a bare expect.
    - Zero hard waits. No `waitForTimeout`, no `sleep`. If you need a wait, you need
      a better locator or `waitForResponse`.
    - User-facing locators: `getByRole`, `getByLabel`, `getByTestId`. Never brittle
      CSS or XPath chains tied to layout.
    - Deterministic state: seed the cart through an API request or a fixture, do not
      click through the UI to arrive at your precondition.
    - `page.route()` interception to stub the pricing/discount API when you want to
      test the frontend in isolation, which is exactly how you catch a UI-layer bug
      without a backend.
    - Tests are independent and parallel-safe. No shared cart, no ordering assumptions.

    ## HOW YOU DELIVER
    You lead with a compact table (Test ID, Level, Type, What it proves, Priority),
    then give the actual runnable code for the tests worth automating. You explicitly
    call out what should stay MANUAL and why, because recommending automation for
    everything is how suites rot. You also state the exit criteria: what must be green
    before this ticket can be closed.""",

    llm=groq_llm,
    verbose=True,
    allow_delegation=False,
)


# ---------------------------------------------------------------------------
# Task 1: Bug Triage
# ---------------------------------------------------------------------------
triage_task = Task(
    description=f"""Triage this bug report from Jira:

{bug_report}

Work through your triage checklist and deliver:
1. SEVERITY: one of S0-S4, with the exact line of the report that justifies it.
2. PRIORITY: one of P0-P4, with the business reasoning (users affected, money at
   risk, workaround available or not). If severity and priority differ, explain why.
3. Do you AGREE with the reporter's severity and the Jira priority as filed? If not,
   state your override and the reason.
4. CATEGORY: exactly one from your taxonomy.
5. AFFECTED COMPONENT / MODULE and the most likely system layer.
6. BUSINESS IMPACT: what it costs if this ships as-is.
7. MISSING INFORMATION: what you would ask the reporter for, and the assumption you
   triaged under in the meantime.
8. CONFIDENCE: High / Medium / Low.""",

    expected_output="""A structured triage verdict in markdown with these headed
    sections: Severity, Priority, Reporter Disagreement, Category, Affected Component,
    Business Impact, Missing Information, Confidence. Each rating must quote the
    evidence line from the bug report that drove it.

    HARD LIMIT: 400 words. This verdict is handed to two more agents, so every
    word you spend costs them room. Use compact bullets, not wide tables.
    Finishing every section matters more than depth in any one of them.""",
    agent=bug_analyst,
)


# ---------------------------------------------------------------------------
# Task 2: Root Cause (uses triage output as context)
# ---------------------------------------------------------------------------
root_cause_task = Task(
    description=f"""Using the triage verdict from the previous task, investigate WHY
this bug happens:

{bug_report}

Deliver:
1. DIFFERENTIAL DIAGNOSIS: what is different between the working case and the
   failing case? Start here.
2. PRIMARY ROOT CAUSE HYPOTHESIS with a confidence percentage, the system layer it
   lives in, the specific function or config that is suspect, and the evidence line
   from the report supporting it.
3. TWO ALTERNATE HYPOTHESES, ranked, each with confidence and evidence.
4. KILL TEST for each of the three: the single fastest check that would disprove it.
5. LAYER VERDICT: frontend, backend, data, infra or third-party, and what the
   evidence lets you EXONERATE.
6. INVESTIGATION STEPS in order, naming the exact log file and grep string, the
   dashboard and metric, the SQL query, the DevTools network call, and the git
   command to diff the suspect release.
7. BLAST RADIUS: what else shares this code path and is probably broken too.
8. WHAT YOU COULD NOT DETERMINE and the one piece of data that would settle it.""",

    expected_output="""A root cause analysis in markdown with: Differential Diagnosis,
    Primary Hypothesis (with confidence % and kill test), Alternate Hypotheses 2 and 3,
    Layer Verdict including what is exonerated, ordered Investigation Steps with named
    artifacts, Blast Radius, and Open Questions.

    HARD LIMIT: 650 words. This analysis is handed to the test strategist, so
    every word you spend costs them room. Use compact bullets, not wide
    markdown tables. Finishing every section matters more than depth in any one
    of them: a complete short report beats a detailed one that gets cut off.""",
    agent=root_cause_agent,
    context=[triage_task],  # Receives output from triage
)


# ---------------------------------------------------------------------------
# Task 3: Test Recommendation (uses both previous outputs)
# ---------------------------------------------------------------------------
test_task = Task(
    description=f"""Using the triage verdict and the root cause analysis from the
previous tasks, design the test strategy for this bug:

{bug_report}

Deliver:
1. THE MISSING TEST: name the single test that should have existed and would have
   caught this before production, and explain why the current suite missed it.
2. VERIFICATION TEST: the one test that proves the fix works. State its level.
3. REGRESSION SET: 3-5 cases that stop this specific bug returning, each pinned to
   the cheapest level that can catch it (unit / API / E2E) with a one-line reason.
4. BOUNDARY AND EDGE CASES: apply boundary value analysis to the failing threshold
   in this report, plus the negative and state-transition cases.
5. PLAYWRIGHT TYPESCRIPT: runnable code for the E2E tests worth automating,
   following your standards (web-first assertions, no hard waits, role/testid
   locators, API-seeded state, route interception where it isolates the layer).
6. WHAT TO KEEP MANUAL and why.
7. EXIT CRITERIA: what must be green before this ticket is closed.""",

    expected_output="""A test strategy in markdown: the Missing Test, a table of tests
    (ID, Level, Type, What it proves, Priority), runnable Playwright TypeScript code
    blocks for the E2E cases, a Manual-only section with justification, and Exit
    Criteria.

    HARD LIMIT: 800 words including the code. You are the last agent and have
    the least room, so budget it: keep the tables narrow, write ONE complete
    Playwright spec file rather than several half-finished ones, and make sure
    you reach Exit Criteria. A complete short plan beats a truncated long one.""",
    agent=test_recommender,
    context=[triage_task, root_cause_task],  # Uses both outputs
)


# ---------------------------------------------------------------------------
# Step 3 + 4 - Assemble the Crew and kick it off
# ---------------------------------------------------------------------------
crew = Crew(
    agents=[bug_analyst, root_cause_agent, test_recommender],
    tasks=[triage_task, root_cause_task, test_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    print(f"\n🔍 QA Bug Triage Crew — Starting Analysis on {BUG_ID}")
    print("=" * 70)

    result = crew.kickoff()

    # crew.kickoff() returns only the LAST task's output when printed directly.
    # result.tasks_output holds every agent's output, in order.
    labels = [
        "AGENT 1 — Senior Bug Triage Analyst (Severity / Priority / Category)",
        "AGENT 2 — Root Cause Investigator (Why it broke, and where)",
        "AGENT 3 — Test Strategy Advisor (How we prove it is fixed)",
    ]

    print("\n\n" + "=" * 70)
    print(f"📋 FINAL TRIAGE REPORT — {BUG_ID}")
    print("=" * 70)

    for label, task_output in zip(labels, result.tasks_output):
        print("\n\n" + "#" * 70)
        print(f"# {label}")
        print("#" * 70 + "\n")
        print(task_output.raw)

    usage = result.token_usage
    print("\n\n" + "=" * 70)
    if usage and usage.total_tokens:
        print(f"✅ Done. Tokens used: {usage}")
    else:
        # FallbackLLM wraps the provider, so CrewAI's usage collector sees the
        # wrapper rather than the provider that actually made the call.
        print("✅ Done. (Token usage is not tracked through the fallback wrapper.)")
    print("=" * 70)