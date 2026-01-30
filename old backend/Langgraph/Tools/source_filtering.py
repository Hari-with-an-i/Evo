import sys
import os
from langchain_core.tools import tool

# Ensure we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from analytics_manager import tool_filter_and_parse, CREDIBLE_SOURCES

@tool
def source_tool(query: str):
    """
    Use this tool to find information from CREDIBLE sources only.
    It performs a search and then filters/parses the results to ensure they are from trusted domains.
    Returns the parsed content from credible articles.
    """
    print(f"--- SOURCE VERIFICATION: {query} ---")
    try:
        from news_fetcher import fetch_news_from_serpapi
        
        # 1. Fetch
        raw_results = fetch_news_from_serpapi(keywords=query, num_results=10)
        
        # 2. Filter & Parse
        # We need to adapt the input for tool_filter_and_parse which expects 'link' key.
        # news_fetcher returns dicts with 'link' usually.
        
        credible_articles = tool_filter_and_parse(raw_results)
        
        if not credible_articles:
            return "No credible articles found for this query."
            
        # 3. Format for agent
        summary = f"Found {len(credible_articles)} credible articles:\n"
        for a in credible_articles:
            summary += f"Source: {a['source']}\nTitle: {a['title']}\nExcerpt: {a['raw_text'][:200]}...\n\n"
            
        return summary

    except Exception as e:
        return f"Error in source verification: {e}"