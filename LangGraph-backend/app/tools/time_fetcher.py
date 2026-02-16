from typing import Union
from langchain_core.tools import tool
from .analytics_manager import tool_fetch_time_series_data

@tool
def time_tool(keywords: str, days: Union[int, str] = 30):
    """
    Use this tool when the user asks for trends over a specific period or mentions "last X days".
    It fetches news articles over the time period to see how the story evolved.
    """
    # Defensive casting for robustness against LLM string outputs
    try:
        days = int(days)
    except (ValueError, TypeError):
        days = 30
        
    print(f"--- TIME TRAVEL: {keywords} for last {days} days ---")
    
    try:
        # We'll use a granularity of 7 days by default for the agent
        articles = tool_fetch_time_series_data(keywords=keywords, time_period_days=days, granularity_days=7)
        if not articles:
            return "No time-series data found."
            
        # Summarize for the agent
        summary = f"Found {len(articles)} articles over the last {days} days.\n"
        # Just return a sample or summary to avoid token limit overflow in the agent context
        # In a real app, you might want to aggregate this properly.
        # For now, let's list the first few.
        for i, a in enumerate(articles[:5]):
             summary += f"- {a.get('time_period', 'Unknown Date')}: {a.get('title', 'No Title')}\n"
             
        return summary

    except Exception as e:
        return f"Error fetching time series: {e}"
