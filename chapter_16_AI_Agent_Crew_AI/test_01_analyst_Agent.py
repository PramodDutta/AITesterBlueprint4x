# Test Ananlyst Agent
#
# a senior QA with 15 years (JIRA MD)
#  of experience. Based on the feature,
# it will just analyze the requirement
# and suggest a 5-10 testcases(p0 testcases).

from crewai import Agent, Task, Crew
from crewai import LLM
from dotenv import load_dotenv
import os

# Step 0 - Set up the Brain (Groq LLM)
load_dotenv()  # reads the .env file in this folder
groq_llm = LLM(
    model=f"openai/{os.getenv('GROQ_MODEL')}",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url=os.getenv("GROQ_BASE_URL"),
)


# Step 1. - Define the Agent (identity)
qa_agent = Agent(
    role="QA Enginner",
    goal="Analyse the feature or the requirements, and create 5-10 test cases out of it.",
    backstory="You are a senior QA engineer with 15 years of experience in test planning and testcases creation",
    llm=groq_llm,
    verbose=True,
)

# Step 2 - Give the Task to the Agent
test_case_create = Task(
    description="Create 5-10 Testcase",
    expected_output="A numbered list of 5-10 test cases with brief descriptions for a app.vwo.com Login page with the username, password and submit button with remember me functionality",
    agent=qa_agent,
)

# Step 3. Add them to the Crew
crew = Crew(agents=[qa_agent], tasks=[test_case_create], verbose=True)


if __name__ == "__main__":
    result = crew.kickoff()
    print(result)
