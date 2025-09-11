# For Sentiment Analysis
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
# We need to import the tool we are going to use
from news_fetcher import fetch_news_from_serpapi
# For Emotion Analysis
from transformers import pipeline
from collections import defaultdict, Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
import google.generativeai as genai
from config import GOOGLE_API_KEY
import json
genai.configure(api_key=GOOGLE_API_KEY)

# --- Tool Initializations ---
# It's much more efficient to load these models once and reuse them.

# 1. Initialize VADER Sentiment Analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()
print("✅ VADER Sentiment Analyzer initialized.")

# 2. Initialize Hugging Face Emotion Analysis Pipeline
# This will download the model the first time it's run.
print("🧠 Loading Emotion Analysis model...")
emotion_pipeline = pipeline(
    "text-classification", 
    model="cardiffnlp/twitter-roberta-base-emotion",
    top_k=1 # Return only the top emotion
)
print("✅ Emotion Analysis model loaded.")


# --- Helper Functions ---

def get_sentiment(text: str) -> float:
    """
    Analyzes text and returns a single sentiment score.
    """
    # VADER's compound score is a single metric from -1 (v. neg) to +1 (v. pos)
    scores = sentiment_analyzer.polarity_scores(text)
    return scores['compound']

def get_emotion(text: str) -> str:
    """
    Analyzes text and returns the dominant emotion.
    """
    try:
        # Truncate text to fit model's max input size
        results = emotion_pipeline(text[:512])
        # The result is a list of lists, we want the label from the first item
        return results[0][0]['label']
    except Exception:
        return "unknown" # Handle potential errors gracefully

# --- Main Tool Function ---

def tool_run_text_analytics(articles: list) -> list:
    """
    The main tool for this module. It takes a list of articles
    and enriches each one with sentiment and emotion data.
    """
    print(f"🔬 Running text analytics on {len(articles)} articles...")
    enriched_articles = []
    for article in articles:
        # Get the raw text, or an empty string if it's missing
        text = article.get("raw_text", "")
        
        # Run the analyses
        sentiment_score = get_sentiment(text)
        dominant_emotion = get_emotion(text)
        
        # Add the new data to the article dictionary
        article['sentiment_score'] = sentiment_score
        article['emotion'] = dominant_emotion
        
        enriched_articles.append(article)
        print(f"  -> Analyzed '{article['title'][:30]}...': Sentiment={sentiment_score}, Emotion='{dominant_emotion}'")
        
    print("✅ Text analysis complete.")
    return enriched_articles

def tool_fetch_time_series_data(keywords: str, time_period_days: int, granularity_days: int) -> list:
    """
    Fetches news articles in chunks over a specified time period.
    """
    print(f"🗓️ Fetching time-series data for '{keywords}' over the last {time_period_days} days.")
    
    all_articles = []
    end_date = datetime.now()

    # Loop backwards in time in chunks (e.g., weekly)
    for i in range(0, time_period_days, granularity_days):
        start_date = end_date - timedelta(days=granularity_days)
        
        # Format dates for the API (e.g., "09/04/2025")
        start_date_str = start_date.strftime("%m/%d/%Y")
        end_date_str = end_date.strftime("%m/%d/%Y")
        
        # Fetch articles for this specific chunk of time
        articles_in_period = fetch_news_from_serpapi(
            keywords=keywords,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        # "Tag" each article with the start date of its period for later grouping
        for article in articles_in_period:
            article['time_period'] = start_date.strftime("%Y-%m-%d")
        
        all_articles.extend(articles_in_period)
        
        # Set the new end_date for the next loop iteration
        end_date = start_date
        
    print(f"✅ Time-series fetch complete. Found a total of {len(all_articles)} articles.")
    return all_articles

# In analytics_manager.py

async def tool_aggregate_analytics(analyzed_articles: list) -> dict:
    """
    Aggregates articles by time period and summarizes the key narratives for each.
    """
    print("📊 Aggregating analytics and identifying narratives...")
    grouped_articles = defaultdict(list)
    for article in analyzed_articles:
        grouped_articles[article['time_period']].append(article)
        
    final_analytics = {}
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    for period, articles in grouped_articles.items():
        print(f"  -> Processing period starting {period} ({len(articles)} articles)")
        
        # Combine text for the period
        corpus = "\n\n---\n\n".join([f"Title: {a['title']}\n{a['raw_text']}" for a in articles])
        
        # Use an LLM to identify the dominant narratives for this period
        narrative_prompt = f"Analyze the following news articles from a single time period. Identify and summarize the 2-3 dominant, distinct narratives or sub-plots. Be specific.\n\nARTICLES:\n{corpus[:15000]}"
        
        try:
            narrative_response = await model.generate_content_async(narrative_prompt)
            narratives = narrative_response.text
        except Exception:
            narratives = "Could not determine narratives for this period."

        # Also calculate sentiment for context
        avg_sentiment = sum(a['sentiment_score'] for a in articles) / len(articles)

        final_analytics[period] = {
            "article_count": len(articles),
            "dominant_narratives": narratives, # This is our new, richer data point
            "average_sentiment_score": round(avg_sentiment, 3),
            "full_text_corpus": corpus # Pass the full text for the final analysis
        }
        
    print("✅ Narrative aggregation complete.")
    return final_analytics

# In analytics_manager.py

async def tool_generate_narrative_report(analytics_data: dict) -> dict:
    """
    Takes aggregated narrative data and uses an LLM to generate a full report.
    """
    print("💡 Generating full media narrative report with LLM...")

    # Format the analytics data into a readable briefing for the prompt
    briefing = ""
    sorted_periods = sorted(analytics_data.keys())
    for period in sorted_periods:
        data = analytics_data[period]
        briefing += f"--- Analysis for Period Starting {period} ---\n"
        briefing += f"Dominant Narratives:\n{data['dominant_narratives']}\n"
        briefing += f"Overall Sentiment Score: {data['average_sentiment_score']}\n"
        briefing += f"Supporting Raw Text for this period:\n{data['full_text_corpus'][:5000]}\n\n"

    # The new, more powerful prompt
    prompt = f"""
    You are a senior media intelligence analyst delivering a high-level briefing. Your analysis must be insightful, professional, and directly supported by the data provided.

    **MEDIA INTELLIGENCE REPORT:**
    {briefing}

    **YOUR TASK:**
    Based on the report, provide a strategic analysis.
    1.  **Trend Analysis:** Analyze the evolution of the news narrative from one period to the next. Explain *why* the narrative might be shifting. **Cite specific, brief examples or quotes from the 'Supporting Raw Text'** to back up your analysis.
    2.  **Sentiment Context:** Briefly explain the overall sentiment and what is likely causing it, based on the narratives. Do not just state the score, interpret its meaning.
    3.  **Viable Mitigation Strategies:** Propose 2-3 distinct and actionable strategies. For each strategy, provide:
        - A clear 'name' for the strategy.
        - A 'description' of the specific actions to take.
        - A 'justification' explaining *why* this strategy is effective against the specific trends you identified in your analysis.

    **OUTPUT FORMAT:**
    You MUST provide your response as a single, valid JSON object. Do not include any text before or after the JSON block. The JSON object must have the keys: "trend_analysis", "sentiment_context", and "mitigation_strategies" (which should be a list of objects).
    """

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = await model.generate_content_async(prompt)
        # Clean the response to ensure it's valid JSON
        cleaned_json_string = response.text.strip().replace("```json", "").replace("```", "")
        report = json.loads(cleaned_json_string)
        print("✅ Full narrative report generated successfully.")
        return report
    except Exception as e:
        print(f"❌ LLM Report Generation Error: {e}")
        # Return the raw text on failure for debugging
        return {"error": "Failed to generate valid JSON report.", "raw_response": response.text}