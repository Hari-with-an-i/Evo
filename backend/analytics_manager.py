import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# --- Local Analysis Tools ---
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

# --- API Tools ---
from groq import Groq
from news_fetcher import fetch_news_from_serpapi
from config import GROQ_API_KEY # Only import the key we need

# ==============================================================================
# 1. INITIALIZE ALL MODELS AND CLIENTS ONCE AT THE TOP
# ==============================================================================

# VADER Sentiment Analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()
print("✅ VADER Sentiment Analyzer initialized.")

# Hugging Face Emotion Analysis Pipeline
print("🧠 Loading Emotion Analysis model...")
emotion_pipeline = pipeline(
    "text-classification", 
    model="cardiffnlp/twitter-roberta-base-emotion",
    top_k=1
)
print("✅ Emotion Analysis model loaded.")

# Groq API Client
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("✅ Groq API client initialized.")
else:
    groq_client = None
    print("❌ Groq API key not found. Narrative generation will be skipped.")

# ==============================================================================
# 2. HELPER AND TOOL FUNCTIONS
# ==============================================================================

def get_sentiment(text: str) -> float:
    scores = sentiment_analyzer.polarity_scores(text)
    return scores['compound']

def get_emotion(text: str) -> str:
    try:
        results = emotion_pipeline(text[:512])
        return results[0][0]['label']
    except Exception:
        return "unknown"

def tool_run_text_analytics(articles: list) -> list:
    print(f"🔬 Running text analytics on {len(articles)} articles...")
    enriched_articles = []
    for article in articles:
        text = article.get("raw_text", "")
        article['sentiment_score'] = get_sentiment(text)
        article['emotion'] = get_emotion(text)
        enriched_articles.append(article)
    print("✅ Text analysis complete.")
    return enriched_articles

def tool_fetch_time_series_data(keywords: str, time_period_days: int, granularity_days: int) -> list:
    print(f"🗓️ Fetching time-series data for '{keywords}'...")
    all_articles = []
    end_date = datetime.now()
    for i in range(0, time_period_days, granularity_days):
        start_date = end_date - timedelta(days=granularity_days)
        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date_str = end_date.strftime("%m/%d/%Y")
        articles_in_period = fetch_news_from_serpapi(keywords=keywords, start_date=start_date_str, end_date=end_date_str)
        for article in articles_in_period:
            article['time_period'] = start_date.strftime("%Y-%m-%d")
        all_articles.extend(articles_in_period)
        end_date = start_date
    print(f"✅ Time-series fetch complete. Found {len(all_articles)} articles.")
    return all_articles

async def tool_aggregate_analytics(analyzed_articles: list) -> dict:
    print("📊 Aggregating analytics and identifying narratives...")
    grouped_articles = defaultdict(list)
    for article in analyzed_articles:
        grouped_articles[article['time_period']].append(article)
        
    final_analytics = {}
    
    if not groq_client:
        print("❌ Groq client not initialized. Skipping narrative aggregation.")
        return final_analytics

    for period, articles in grouped_articles.items():
        print(f"  -> Processing period starting {period} ({len(articles)} articles)")
        corpus = "\n\n---\n\n".join([f"Title: {a['title']}\n{a['raw_text']}" for a in articles])
        avg_sentiment = sum(a['sentiment_score'] for a in articles) / len(articles)
        
        narrative_prompt = f"Analyze the following news articles from a single time period. Identify and summarize the 2-3 dominant, distinct narratives or sub-plots. Be specific and concise.\n\nARTICLES:\n{corpus[:12000]}"
        
        try:
            # --- THIS IS THE FIX ---
            # Using a valid, fast model for this aggregation step
            chat_completion = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": narrative_prompt}],
                model="llama3-8b-8192" 
            )
            narratives = chat_completion.choices[0].message.content
        except Exception as e:
            print(f"❌ Groq narrative generation error: {e}")
            narratives = "Could not determine narratives for this period due to an API error."
        # --- END OF FIX ---

        final_analytics[period] = {
            "article_count": len(articles),
            "dominant_narratives": narratives,
            "average_sentiment_score": round(avg_sentiment, 3),
            "full_text_corpus": corpus
        }
        
    print("✅ Narrative aggregation complete.")
    return final_analytics

async def tool_generate_narrative_report(analytics_data: dict) -> dict:
    if not groq_client:
        return {"error": "Groq API key is not configured."}
    
    print("💡 Generating full media narrative report with Groq API...")
    briefing = ""
    sorted_periods = sorted(analytics_data.keys())
    for period in sorted_periods:
        data = analytics_data[period]
        briefing += f"--- Analysis for Period Starting {period} ---\n"
        briefing += f"Dominant Narratives:\n{data['dominant_narratives']}\n"
        briefing += f"Overall Sentiment Score: {data['average_sentiment_score']}\n"
        briefing += f"Supporting Raw Text for this period:\n{data['full_text_corpus'][:5000]}\n\n"

    # This prompt is correct and matches your frontend (executive_summary, analysis_of_trend)
    prompt = f"""
    You are a senior media intelligence analyst delivering a high-level briefing.

    **MEDIA INTELLIGENCE REPORT:**
    {briefing}

    **YOUR TASK:**
    Analyze the report and generate a response in a strict JSON format. The JSON object MUST contain the following three top-level keys: "executive_summary", "analysis_of_trend", and "mitigation_strategies".

    - For "executive_summary", provide a concise, top-level summary of the public perception trend.
    - For "analysis_of_trend", analyze the evolution of the news narrative. Explain the "why" and cite specific examples from the 'Supporting Raw Text'.
    - For "mitigation_strategies", propose 3 distinct strategies, each as an object with "name", "description", and "justification".

    **IMPORTANT:** Your entire output must be a single, valid JSON object and nothing else.
    """

    response_text = None # Initialize to handle errors
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            # --- THIS IS THE FIX ---
            # Using the valid, powerful model for the final report
            model="llama-3.3-70b-versatile", 
            response_format={"type": "json_object"},
        )
        response_text = chat_completion.choices[0].message.content
        report = json.loads(response_text)
        print("✅ Full narrative report generated successfully by Groq.")
        return report
    except Exception as e:
        print(f"❌ Groq API Report Generation Error: {e}")
        return {"error": "Failed to generate valid JSON report.", "raw_response": response_text, "details": str(e)}