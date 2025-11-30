import json
import os
import urllib.parse
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional


from analytics_manager import (
    tool_fetch_time_series_data, 
    tool_run_text_analytics,
    tool_aggregate_analytics, # <-- Import the new tool
    tool_generate_narrative_report,
    generate_counterspeech_with_evidence
)

# Import your custom tool for fetching news
from news_fetcher import fetch_news_from_serpapi
from config import GOOGLE_API_KEY, SERPAPI_KEY

# --- Configuration & Setup ---
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")

# 1. CREDIBILITY FILTER: Define your list of trusted news sources
# The agent will only parse articles from these domains.
CREDIBLE_SOURCES = {
    'reuters.com',
    'apnews.com',
    'bbc.com',
    'nytimes.com',
    'wsj.com',
    'washingtonpost.com',
    'theguardian.com',
    'npr.org',
    'aljazeera.com',
    'cnbc.com',
    'bloomberg.com',
    'forbes.com',
    'thehindu.com',
    'timesofindia.indiatimes.com',
    'ign.com',
    'gamespot.com',
    'gamesradar.com',
    'pcgamer.com',
    'gamingbolt.com'}

app = FastAPI(title="News Analysis Agent")

origins = [
    "http://localhost:5173", # The default Vite dev server address
    "http://localhost:3000", # The default create-react-app address
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allow all methods (GET, POST, etc.)
    allow_headers=["*"], # Allow all headers
)


class AnalysisRequest(BaseModel):
    query: str # The user's natural language query

class TrendAnalysisRequest(BaseModel):
    keywords: str
    time_period_days: int = 30 # Default to analyzing the last 30 days
    granularity_days: int = 7   # Analyze in 7-day (weekly) chunks

class CounterspeechRequest(BaseModel):
    statement: str
    days_back: Optional[int] = 30
    top_k: Optional[int] = 3
    # optional manual keywords override (if you want to force the search terms)
    keywords: Optional[str] = None



# --- Agent Tools ---

@app.post("/generate-counterspeech", include_in_schema=True)
async def generate_counterspeech_api(payload: CounterspeechRequest):
    """
    Generate a short counterspeech plus relevant news evidence.
    """
    # Basic validation
    if not payload.statement or not payload.statement.strip():
        raise HTTPException(status_code=400, detail="`statement` must be a non-empty string.")

    try:
        # Call the counterspeech generator (sync function)
        result = await generate_counterspeech_with_evidence(
            statement=payload.statement,
            days_back=payload.days_back,
            top_k=payload.top_k,
            keywords=payload.keywords
        )

        # If your function returns an error structure, map it to HTTP error
        if not result or "counterspeech" not in result:
            raise HTTPException(status_code=500, detail="Failed to generate counterspeech.")

        return {"status": "success", "result": result}

    except Exception as e:
        # Log error server-side
        print(f"❌ Counterspeech generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))



async def tool_extract_keyword(user_query: str) -> str:
    """
    Uses an LLM to distill a user's query into a clean, searchable keyword/phrase.
    """
    print(f"🤖 Using LLM to extract keyword from: '{user_query}'")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            "You are an expert search query analyst. "
            "Analyze the following user query and extract the core, neutral topic or keyword phrase. "
            "The output should be a clean search term only, with no extra explanation. "
            f"QUERY: '{user_query}'"
        )
        response = await model.generate_content_async(prompt)
        keyword = response.text.strip()
        print(f"✅ Extracted Keyword: '{keyword}'")
        return keyword
    except Exception as e:
        print(f"❌ LLM Keyword Extraction Error: {e}")
        # Fallback to using the raw query if LLM fails
        return user_query

def tool_filter_and_parse(articles_from_api: list) -> list[dict]:
    """
    Filters articles for credible sources and then parses them to get raw text.
    """
    print(f"🔧 Filtering and Parsing {len(articles_from_api)} articles...")
    from newspaper import Article # Import here to keep it contained

    cleaned_articles = []
    for article_data in articles_from_api:
        link = article_data.get("link")
        if not link:
            continue
            
        domain = urllib.parse.urlparse(link).netloc.replace('www.', '')

        if domain in CREDIBLE_SOURCES:
            print(f"  👍 Credible source found: {domain}. Parsing...")
            try:
                article = Article(url=link)
                article.download()
                article.parse()
                if article.text:
                    cleaned_articles.append({
                        "source": domain,
                        "url": link,
                        "title": article.title,
                        "raw_text": article.text,
                        # --- THIS IS THE FIX ---
                        "time_period": article_data.get("time_period")
                    })
            except Exception as e:
                print(f"  ❌ Failed to parse {link}: {e}")
        else:
            print(f"  👎 Skipping non-credible source: {domain}")
    
    print(f"🧹 Process complete. Stored raw text from {len(cleaned_articles)} credible articles.")
    return cleaned_articles

@app.post("/analyze-perception-trend")
async def analyze_perception_trend(request: TrendAnalysisRequest):
    """
    Analyzes sentiment and topic trends over time and suggests mitigation.
    """
    # Step 1: Fetch all article METADATA (links, titles, etc.) over the time period
    time_series_articles_metadata = tool_fetch_time_series_data(
        keywords=request.keywords,
        time_period_days=request.time_period_days,
        granularity_days=request.granularity_days
    )
    if not time_series_articles_metadata:
        raise HTTPException(status_code=404, detail="No articles found for the specified topic and time range.")

    # --- ADD THIS NEW STEP ---
    # Step 1.5: Parse the articles to get the 'raw_text'
    parsed_articles = tool_filter_and_parse(time_series_articles_metadata)
    if not parsed_articles:
        raise HTTPException(status_code=404, detail="Could not parse any credible articles in the specified time range.")
    # --- END OF NEW STEP ---

    # Step 2: Run sentiment and emotion analysis on the FULLY PARSED articles
    analyzed_articles = tool_run_text_analytics(parsed_articles)
    
    # Step 3: Aggregate the results into time-based insights
    aggregated_narratives = await tool_aggregate_analytics(analyzed_articles)
    
    # Step 4: Generate the final report
    final_report = await tool_generate_narrative_report(aggregated_narratives)
    
    return {
        "status": "success",
        "keywords": request.keywords,
        "report": final_report,
        "time_series_analytics": aggregated_narratives
    }

