import asyncio
import time
from dotenv import load_dotenv
from langchain.agents import create_agent

load_dotenv()
agent = create_agent(
    model="google_genai:gemini-flash-lite-latest",
    system_prompt=(
        "You are an experienced software testing instructor. "
        "Explain each concept in 10 bullet points"
    ),
)


questions = [
    {"id": 0, "topic": "LLM Eval", "prompt": "What is llm Eval?"},
    {"id": 1, "topic": "Smoke Testing", "prompt": "What is smoke testing?"},
    {"id": 2, "topic": "Sanity Testing", "prompt": "What is sanity testing?"},
    {"id": 3, "topic": "Regression Testing", "prompt": "What is regression testing?"},
]

async def main():
    print("Creating LangChain agent...\n")
    start = time.perf_counter()

    # asyncio.gather runs every agent.ainvoke() call CONCURRENTLY
    results = await asyncio.gather(*[
        agent.ainvoke({"messages": [{"role": "user", "content": q["prompt"]}]})
        for q in questions
    ])

    # results come back in the same order as the questions list
    for q, result in zip(questions, results):
        print(f"{q['id']}. {q['topic']}")
        print(result["messages"][-1].content)
        print("-" * 70)

    print(f"Finished {len(questions)} calls in {time.perf_counter() - start:.1f}s")


asyncio.run(main())