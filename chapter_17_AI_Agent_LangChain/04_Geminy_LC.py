import os

from dotenv import load_dotenv
from langchain.agents import create_agent

load_dotenv()

def main():
    agent = create_agent(model=os.environ["GEMINI_LLM_MODEL"])
    query = input("Ask your question: ")
    result = agent.invoke({"messages": [("user", query)]})
    print(result["messages"][-1].text)

if __name__ == "__main__":
    main()