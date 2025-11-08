import os
import urllib.parse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from typing import Optional

# --- Core Imports for Trend Analysis ---
from analytics_manager import (
    tool_fetch_time_series_data, 
    tool_run_text_analytics,
    tool_aggregate_analytics,
    tool_generate_narrative_report,
    generate_counterspeech_with_evidence  # <-- Add this line
)
from news_fetcher import fetch_news_from_serpapi
from config import SERPAPI_KEY # No longer need Google API key here

# --- Configuration & Setup ---
load_dotenv()

# 1. CREDIBILITY FILTER: Define your list of trusted news sources
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
    'gamingbolt.com'
}

app = FastAPI(title="Evo: Perception Trend Analysis")

# --- CORS Middleware ---
origins = [
    "http://localhost:5173", # Vite
    "http://localhost:3000", # create-react-app
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models ---
class TrendAnalysisRequest(BaseModel):
    keywords: str
    time_period_days: int = 30
    granularity_days: int = 7

class CounterspeechRequest(BaseModel):
    statement: str
    days_back: Optional[int] = 30
    top_k: Optional[int] = 3
    # optional manual keywords override (if you want to force the search terms)
    keywords: Optional[str] = None

@app.post("/generate-counterspeech")
def generate_counterspeech_api(payload: CounterspeechRequest):
    """
    Generate a short counterspeech plus relevant news evidence.
    """
    # Basic validation
    if not payload.statement or not payload.statement.strip():
        raise HTTPException(status_code=400, detail="`statement` must be a non-empty string.")

    try:
        # Call the counterspeech generator (sync function)
        result = generate_counterspeech_with_evidence(
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
    

# --- Helper Tools ---
def tool_filter_and_parse(articles_from_api: list) -> list[dict]:
    """
    Filters articles for credible sources and then parses them to get raw text.
    """
    print(f"🔧 Filtering and Parsing {len(articles_from_api)} articles...")
    from newspaper import Article

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
                        "time_period": article_data.get("time_period")
                    })
            except Exception as e:
                print(f"  ❌ Failed to parse {link}: {e}")
        else:
            print(f"  👎 Skipping non-credible source: {domain}")
    
    print(f"🧹 Process complete. Stored raw text from {len(cleaned_articles)} credible articles.")
    return cleaned_articles

# --- Main Analytics Endpoint ---
@app.post("/analyze-perception-trend")
async def analyze_perception_trend(request: TrendAnalysisRequest):
    """
    Analyzes sentiment and topic trends over time and suggests mitigation.
    """
    # Step 1: Fetch all article METADATA over the time period
    time_series_articles_metadata = tool_fetch_time_series_data(
        keywords=request.keywords,
        time_period_days=request.time_period_days,
        granularity_days=request.granularity_days
    )
    if not time_series_articles_metadata:
        raise HTTPException(status_code=404, detail="No articles found for the specified topic and time range.")

    # Step 2: Parse the articles to get the 'raw_text'
    parsed_articles = tool_filter_and_parse(time_series_articles_metadata)
    if not parsed_articles:
        raise HTTPException(status_code=404, detail="Could not parse any credible articles in the specified time range.")

    # Step 3: Run local sentiment/emotion analysis
    analyzed_articles = tool_run_text_analytics(parsed_articles)
    
    # Step 4: Aggregate narratives using the LLM
    aggregated_narratives = await tool_aggregate_analytics(analyzed_articles)
    
    # Step 5: Generate the final report using the LLM
    final_report = await tool_generate_narrative_report(aggregated_narratives)
    
    return {
        "status": "success",
        "keywords": request.keywords,
        "report": final_report,
        "time_series_analytics": aggregated_narratives
    }