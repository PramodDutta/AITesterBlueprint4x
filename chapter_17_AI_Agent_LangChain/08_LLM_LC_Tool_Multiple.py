from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import InMemorySaver


load_dotenv()

@tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@tool
def sub(a: int, b: int) -> int:
    """Add two numbers."""
    return a - b

@tool
def mul(a: int, b: int) -> int:
    """Add two numbers."""
    return a * b

agent = create_agent(
    model=ChatGroq(model="openai/gpt-oss-120b", temperature=0),
    checkpointer=InMemorySaver(),
    tools=[add,sub,mul]
)
# The same thread_id keeps conversation memory while the program runs.
config = {"configurable": {"thread_id": "demo"}}

for question in [
    "My name is Pramod. Use the add tool for 5 - 3.",
    "What is my name and what was the result?",
]:result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config,
    )


print(result["messages"][-1].content)