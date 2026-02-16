from langchain_core.tools import tool
from .analytics_manager import tool_filter_and_parse, CREDIBLE_SOURCES
from .news_fetcher import fetch_news_from_serpapi

@tool
def source_tool(query: str):
    """
    Use this tool to find information from CREDIBLE sources only.
    It performs a search and then filters/parses the results to ensure they are from trusted domains.
    Returns the parsed content from credible articles.
    """
    print(f"--- SOURCE VERIFICATION: {query} ---")
    try:
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
            summary += f"Source: {a.get('source', 'Unknown')}\nTitle: {a.get('title', 'No Title')}\nExcerpt: {str(a.get('raw_text', ''))[:200]}...\n\n"
            
        return summary

    except Exception as e:
        return f"Error in source verification: {e}"