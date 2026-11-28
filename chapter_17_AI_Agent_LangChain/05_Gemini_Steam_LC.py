import os
from dotenv import load_dotenv
from langchain.agents import create_agent

load_dotenv()


def main():
    agent = create_agent(model=os.environ["GEMINI_LLM_MODEL"])
    # query = input("Ask your question: ")
    print("\nStreaming Response:")
    for token, metadata in agent.stream(
        {
            "messages": [
                {"role": "system", "content": "You are a software testing instructor."},
                {"role": "user", "content": "Explain LLM Eval in 1000 words blog"},
            ]
        },
        stream_mode="messages",
    ):
        print(token.text, end="", flush=True)
    print()


if __name__ == "__main__":
    main()