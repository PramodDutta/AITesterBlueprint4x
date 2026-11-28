from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma3:270m",
    temperature=0,
)

messages = [
    (
        "system",
        "You are a helpful assistant ",
    ),
    ("human", "program to reverse string in python"),
]
ai_msg = llm.invoke(messages)
print(ai_msg.content_blocks)