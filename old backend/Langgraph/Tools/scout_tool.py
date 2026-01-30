import sys
import os

# Ensure we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from langchain_core.tools import tool
from news_fetcher import fetch_news_from_serpapi

@tool
def scout_tool(query: str):
    """
    Primary research tool. Use this FIRST for almost every user request.
    It performs a broad search to gather initial context, news snippets, and facts.
    Returns a list of raw text snippets related to the query.
    """
    print(f"--- SCOUTING: {query} ---")
    
    try:
        results = fetch_news_from_serpapi(keywords=query, num_results=5)
        if not results:
            return ["No results found."]
        
        # Return a simplified list of strings for the agent
        snippets = []
        for r in results:
            title = r.get("title", "No Title")
            source = r.get("source", "Unknown Source")
            snippet = r.get("snippet", r.get("date", ""))
            snippets.append(f"Title: {title}\nSource: {source}\nSnippet: {snippet}\n")
            
        return snippets
            
    except Exception as e:
        return [f"Error searching for {query}: {e}"]