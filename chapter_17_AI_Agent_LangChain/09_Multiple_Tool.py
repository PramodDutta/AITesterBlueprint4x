import re
import requests                            # call external APIs and pages
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool

load_dotenv()
HEADERS = {"User-Agent": "Mozilla/5.0"}


# Tool 1: search the web and return the title of the results page
@tool
def search_tool(query: str) -> str:
    """Search the web for a query and return the title of the results page."""
    try:
        res = requests.get("https://html.duckduckgo.com/html/",
                           params={"q": query}, headers=HEADERS, timeout=10)
        match = re.search(r"<title>(.*?)</title>", res.text, re.S)
        return match.group(1).strip() if match else "No title found"
    except Exception:
        return "Error performing search"


# Tool 2: fetch a URL and return its plain text (first 1000 characters)
@tool
def web_content_tool(url: str) -> str:
    """Fetch the content of a web page from a URL and return its plain text."""
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        text = re.sub(r"<[^>]*>", "", res.text)   # strip HTML tags
        return text[:1000]
    except Exception:
        return "Error fetching web content"


agent = create_agent(
    model="google_genai:gemini-flash-lite-latest",
    tools=[search_tool, web_content_tool],  # pass both tools in the list
    system_prompt=(
        "You are a helpful automation testing assistant. "
        "Use the available tools to search the web and fetch content when needed."
    ),
)

queries = [
    "What is Playwright?",   
    "Search for the TheTestingAcademy", # needs web_content_tool                             # general info (may use search)
    "Search for the Appium official website",             # needs search_tool
    "Get content from https://playwright.dev/docs/intro", # needs web_content_tool
]

for q in queries:
    print(f"\nQ: {q}")
    result = agent.invoke({"messages": [{"role": "user", "content": q}]})
    print(f"Agent: {result['messages'][-1].content}")