import sys
import os
import asyncio
from langchain_core.tools import tool

# Ensure we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from analytics_manager import tool_generate_narrative_report, tool_aggregate_analytics, tool_run_text_analytics

@tool
def report_tool(analytics_data_str: str):
    """
    Generates a full narrative report based on aggregated analytics data.
    NOTE: In a real agent, this might take a complex object. 
    For simplicity here, we assume the agent calls this as a final step if it has data.
    Or, more likely, this tool might actually triggering the full pipeline for a topic.
    
    Let's make this tool a "Deep Dive" tool that does the full pipeline for a topic if the user asks for a report.
    """
    # This is a bit tricky as the input needs to be a dict. 
    # Tools usually take strings. 
    # Let's pivot: This tool takes a topic, and runs the FULL pipeline (fetch -> analyze -> report).
    return "Please use 'scout_tool' or 'time_tool' to gather data first, then I can summarize it. (Not fully implemented for direct agent use yet)"

# Redefining to be a "Generate Report for Topic" tool
@tool
def narrative_report_tool(topic: str):
    """
    Generates a comprehensive narrative report and mitigation strategies for a specific topic.
    This runs the full pipeline: Fetch time-series data -> Analyze Sentiment -> Generate Report.
    Use this when the user asks for a "report", "briefing", or "strategy" on a topic.
    """
    print(f"--- GENERATING REPORT FOR: {topic} ---")
    
    # We need to call the async functions from analytics_manager.
    # We can use asyncio.run() or if existing loop, just await.
    # Since tools are often synchronous in LangChain (unless async agent), we'll try to run sync.
    
    try:
        from analytics_manager import tool_fetch_time_series_data, tool_filter_and_parse 
        
        # Helper to run async functions
        def run_sync(coro):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            res = loop.run_until_complete(coro)
            loop.close()
            return res

        # 1. Fetch Time Series Data (Sync)
        print(f"  Fetching data for {topic}...")
        results = tool_fetch_time_series_data(keywords=topic, time_period_days=30, granularity_days=7)
        
        # 2. Filter & Parse (Sync)
        print(f"  Parsing credible sources...")
        parsed = tool_filter_and_parse(results)
        
        if not parsed:
            return "No credible data found to generate a report."
            
        # 3. Run Analytics (Sync)
        print(f"  Running analytics...")
        analyzed = tool_run_text_analytics(parsed)
        
        # 4. Aggregate (Async)
        print(f"  Aggregating...")
        # aggregated = await tool_aggregate_analytics(analyzed)
        try:
             aggregated = run_sync(tool_aggregate_analytics(analyzed))
        except RuntimeError:
             # Already in loop?
             # This is the tricky part of calling async code from sync tool in async FastAPI.
             return "Error: Async loop conflict. Agent needs to be configured for async tools."

        # 5. Generate Report (Async)
        print(f"  Generating final report...")
        # report = await tool_generate_narrative_report(aggregated)
        try:
            report = run_sync(tool_generate_narrative_report(aggregated))
        except RuntimeError:
            return "Error: Async loop conflict."
        
        # If report is dict with keys, format it for LLM
        if isinstance(report, dict):
            summary = report.get("executive_summary", "")
            trend = report.get("analysis_of_trend", "")
            strategies = report.get("mitigation_strategies", [])
            
            formatted = f"**Executive Summary**\n{summary}\n\n**Trend Analysis**\n{trend}\n\n**Strategies**\n"
            if isinstance(strategies, list):
                for s in strategies:
                    formatted += f"- {s.get('name')}: {s.get('description')}\n"
            else:
                formatted += str(strategies)
            return formatted
            
        return str(report)

    except Exception as e:
        return f"Error generating report: {e}"