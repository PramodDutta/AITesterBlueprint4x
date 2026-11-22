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
import os
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
    pass

# Agent 1: Bug Triage Analyst
bug_analyst = Agent()
# Agent 2: Root Cause Investigator
root_cause_agent = Agent()
# Agent 3: Test Recommendation Agent
test_recommender = Agent()

# Task 1: Bug Triage
triage_task = Task()

# Task 2: Investigate root cause (uses triage output as context)
root_cause_task = Task()

# Task 3: Recommend Test
test_task = Task()


crew = Crew(
    agents=[bug_analyst, root_cause_agent, test_recommender],
    tasks=[triage_task, root_cause_task, test_task],
    process=Process.sequential,
    verbose=True
)

print("🔍 QA Bug Triage Crew — Starting Analysis")
print("=" * 60)

result = crew.kickoff()
print("\n" + "=" * 60)
print("📋 FINAL TRIAGE REPORT")
print("=" * 60)
print(result)