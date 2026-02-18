import asyncio
from langchain_core.tools import tool
from .analytics_manager import tool_generate_narrative_report, tool_aggregate_analytics, tool_run_text_analytics, tool_fetch_time_series_data, tool_filter_and_parse

@tool
def narrative_report_tool(topic: str):
    """
    Generates a comprehensive narrative report and mitigation strategies for a specific topic.
    This runs the full pipeline: Fetch time-series data -> Analyze Sentiment -> Generate Report.
    Use this when the user asks for a "report", "briefing", or "strategy" on a topic.
    """
    print(f"--- GENERATING REPORT FOR: {topic} ---")
    
    try:
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
        try:
             aggregated = run_sync(tool_aggregate_analytics(analyzed))
        except RuntimeError:
             return "Error: Async loop conflict. Agent needs to be configured for async tools."

        # 5. Generate Report (Async)
        print(f"  Generating final report...")
        try:
            report = run_sync(tool_generate_narrative_report(aggregated))
        except RuntimeError:
            return "Error: Async loop conflict."
        
        # If report is dict with keys, format it for LLM
            # Return the raw dictionary so the aggregator can use it
            return report
            
        return str(report)

    except Exception as e:
        return f"Error generating report: {e}"
