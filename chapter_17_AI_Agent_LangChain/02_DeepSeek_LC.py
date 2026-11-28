from langchain_deepseek import ChatDeepSeek

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

messages = [
    ("system", "You are a helpful coding assistant."),
    ("human", "Write a Python function to reverse a string."),
]

response = llm.invoke(messages)
print(response.content)
