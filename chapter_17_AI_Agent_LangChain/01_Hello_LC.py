from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os

load_dotenv()

def main():
    llm = ChatGroq(model=os.getenv('LLM_MODEL'), temperature=1)
    query = input("Enter a question related to qa")
    response = llm.invoke(query)
    print(response)

if __name__ == "__main__":
    main()