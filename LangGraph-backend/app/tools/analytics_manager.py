import json
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from heapq import nlargest

# --- Local Analysis Tools ---
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline, logging
from google import genai

# --- API Tools ---
from groq import Groq
from .news_fetcher import fetch_news_from_serpapi
from app.config import GROQ_API_KEY, SERPAPI_KEY, GOOGLE_API_KEY

import os

# ==============================================================================
# 1. INITIALIZE ALL MODELS AND CLIENTS ONCE AT THE TOP
# ==============================================================================

# VADER Sentiment Analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()
print("[SUCCESS] VADER Sentiment Analyzer initialized.")

# Hugging Face Emotion Analysis Pipeline
print("[INFO] Loading Emotion Analysis model...")

emotion_pipeline = pipeline(
    "text-classification", 
    model="cardiffnlp/twitter-roberta-base-emotion",
    top_k=1
)
logging.set_verbosity_warning()
print("[SUCCESS] Emotion Analysis model loaded.")

# Groq API Client
if GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    print("[SUCCESS] Groq API client initialized.")
else:
    groq_client = None
    print("[ERROR] Groq API key not found. Narrative generation will be skipped.")

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
    print(f"[INFO] Running text analytics on {len(articles)} articles...")
    for article in articles:
        text = article.get("raw_text", "")
        article['sentiment_score'] = get_sentiment(text)
        article['emotion'] = get_emotion(text)
    print("[SUCCESS] Text analysis complete.")
    return articles

# --- Added for Source Filtering ---

CREDIBLE_SOURCES = [
    "reuters", "apnews", "bbc", "npr", "pbs", "bloomberg", 
    "wsj", "nytimes", "washingtonpost", "economist", "ft.com",
    "nature.com", "sciencemag", "who.int", "un.org"
]

def tool_filter_and_parse(articles: list) -> list:
    print(f"[INFO] Filtering {len(articles)} articles for credible sources...")
    credible_articles = []
    
    for article in articles:
        # Check source name or URL
        source = str(article.get("source", "")).lower()
        url = str(article.get("link", "")).lower()
        
        is_credible = any(cs in source or cs in url for cs in CREDIBLE_SOURCES)
        
        if is_credible:
            # Ensure raw text is present (if not, maybe just use snippet)
            if not article.get("raw_text"):
                article["raw_text"] = article.get("snippet", "")
            credible_articles.append(article)
            
    print(f"[SUCCESS] Found {len(credible_articles)} credible articles.")
    return credible_articles

def tool_fetch_time_series_data(keywords: str, time_period_days: int, granularity_days: int) -> list:
    print(f"[INFO] Fetching time-series data for '{keywords}'...")
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
    print(f"[SUCCESS] Time-series fetch complete. Found {len(all_articles)} articles.")
    return all_articles

async def tool_aggregate_analytics(analyzed_articles: list) -> dict:
    print("[INFO] Aggregating analytics and identifying narratives...")
    grouped_articles = defaultdict(list)
    for article in analyzed_articles:
        grouped_articles[article['time_period']].append(article)
        
    final_analytics = {}
    
    for period, articles in grouped_articles.items():
        print(f"  -> Processing period starting {period} ({len(articles)} articles)")
        corpus = "\n\n---\n\n".join([f"Title: {a['title']}\n{a['raw_text']}" for a in articles])
        avg_sentiment = sum(a['sentiment_score'] for a in articles) / len(articles)
        
        narratives = "Could not determine narratives (Groq client not initialized)."
        if groq_client:
            narrative_prompt = f"Analyze the following news articles from a single time period. Identify and summarize the 2-3 dominant, distinct narratives or sub-plots. Be specific and concise.\n\nARTICLES:\n{corpus[:12000]}"
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": narrative_prompt}],
                    model="llama-3.3-70b-versatile"
                )
                narratives = chat_completion.choices[0].message.content
            except Exception as e:
                print(f"[ERROR] Groq narrative generation error: {e}")
                narratives = "Could not determine narratives for this period due to an API error."
        
        final_analytics[period] = {
            "article_count": len(articles),
            "dominant_narratives": narratives,
            "average_sentiment_score": round(avg_sentiment, 3),
            "full_text_corpus": corpus
        }
        
    print("[SUCCESS] Narrative aggregation complete.")
    return final_analytics

async def tool_generate_narrative_report(analytics_data: dict) -> dict:
    if not groq_client:
        return {"error": "Groq API key is not configured."}
    
    print("[INFO] Generating full media narrative report with Groq API...")
    
    briefing = ""
    sorted_periods = sorted(analytics_data.keys())
    for period in sorted_periods:
        data = analytics_data[period]
        briefing += f"--- Analysis for Period Starting {period} ---\n"
        briefing += f"Dominant Narratives:\n{data['dominant_narratives']}\n"
        briefing += f"Overall Sentiment Score: {data['average_sentiment_score']}\n"
        briefing += f"Supporting Raw Text for this period:\n{data['full_text_corpus'][:5000]}\n\n"

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

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
        )
        report_string = chat_completion.choices[0].message.content
        report = json.loads(report_string)
        print("[SUCCESS] Full narrative report generated successfully by Groq.")
        return report
    except Exception as e:
        print(f"[ERROR] Groq API Report Generation Error: {e}")
        return {"error": "Failed to generate report from Groq API.", "details": str(e)}

def tool_extract_keyword(user_query: str) -> str:
    print(f"[INFO] Using LLM to extract keyword from: '{user_query}'")
    try:
        # Initialize the client with the API key from config/env
        client = genai.Client(api_key=GOOGLE_API_KEY)
        prompt = (
            "You are an expert search query analyst. "
            "Analyze the following user query and extract the core, neutral topic or keyword phrase. "
            "The output should be a clean search term only, with no extra explanation. "
            f"QUERY: '{user_query}'"
        )
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        keyword = response.text.strip()
        print(f"[SUCCESS] Extracted Keyword: '{keyword}'")
        return keyword
    except Exception as e:
        print(f"[ERROR] LLM Keyword Extraction Error: {e}")
        return user_query

def _score_article_relevance(article: dict, query: str) -> float:
    text = (article.get("title", "") + " " + article.get("raw_text", "")).lower()
    qterms = [
        t for t in re.findall(r"\b[a-zA-Z']{3,}\b", query.lower())
        if len(t) > 2
    ]
    if not qterms:
        return 0.0

    count = sum(text.count(t) for t in qterms)

    date_str = (
        article.get("published_at")
        or article.get("date")
        or article.get("time_period")
    )
    recency_weight = 1.0
    try:
        if date_str:
            dt = datetime.fromisoformat(str(date_str)[:10])
            days_old = (datetime.now() - dt).days
            recency_weight = 1.0 / (1 + days_old / 30)
    except Exception:
        recency_weight = 1.0

    return count * recency_weight
    
async def generate_counterspeech_with_evidence(
    statement: str,
    days_back: int = 30,
    top_k: int = 3,
    keywords: str | None = None
) -> dict:
    # 1) Prepare keywords
    if keywords is None or not keywords.strip():
        search_query = tool_extract_keyword(statement)
    else:
        cleaned = " ".join(
            [w for w in re.findall(r"\b[a-zA-Z']{3,}\b", keywords.lower())]
        )
        if len(cleaned.split()) >= 2 or len(cleaned) >= 8:
            search_query = cleaned
        else:
            print(
                f"[WARNING] Ignoring weak user keywords '{keywords}'. "
                "Using auto-extracted query instead."
            )
            search_query = tool_extract_keyword(statement)

    print(f"[SEARCH] Counterspeech search query: '{search_query}' (days_back={days_back})")
    if not SERPAPI_KEY:
        print(
            "[WARNING] SERPAPI key not configured (SERPAPI_KEY is empty). "
            "fetch_news_from_serpapi will likely return no results."
        )

    # 3) Fetch recent articles
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    start_date_str = start_date.strftime("%m/%d/%Y")
    end_date_str = end_date.strftime("%m/%d/%Y")

    print(
        f"[SEARCH] Attempting news fetch (primary) for: "
        f"'{search_query}' from {start_date_str} to {end_date_str}"
    )
    try:
        articles = fetch_news_from_serpapi(
            keywords=search_query,
            start_date=start_date_str,
            end_date=end_date_str,
            num_results=10,
        )
    except TypeError:
        articles = fetch_news_from_serpapi(
            keywords=search_query,
            start_date=start_date_str,
            end_date=end_date_str,
        )
    except Exception as e:
        print(f"[ERROR] Error fetching news (primary): {e}")
        articles = []

    # Fallback: broader search
    if not articles:
        print("[WARNING] Primary fetch returned zero articles. Trying a broader fetch...")
        try:
            articles = fetch_news_from_serpapi(keywords=search_query, num_results=50)
        except Exception as e:
            print(f"[ERROR] Error fetching news (broader): {e}")
            articles = []

    # Fallback: hardcoded query
    if not articles:
        fallback_query = "ai jobs automation impact employment"
        print(f"[WARNING] Broader fetch failed. Trying fallback query: '{fallback_query}'")
        try:
            articles = fetch_news_from_serpapi(keywords=fallback_query, num_results=50)
        except Exception as e:
            print(f"[ERROR] Error fetching news (fallback): {e}")
            articles = []

    print(f"[SEARCH] Fetch complete. Retrieved {len(articles)} raw article(s).")
    if articles:
        sample_titles = [a.get("title") for a in articles[:5]]
        print("[NEWS] Sample titles:", sample_titles)

    # Ensure raw_text exists
    for a in articles:
        if not a.get("raw_text") and a.get("snippet"):
            a["raw_text"] = a["snippet"]
        if not a.get("raw_text"):
            a["raw_text"] = a.get("title", "")

    # 4) Run analytics
    try:
        articles = tool_run_text_analytics(articles)
    except Exception as e:
        print(f"[WARNING] Text analytics failed: {e}")

    # 5) Score & select top_k
    scored = []
    for a in articles:
        score = _score_article_relevance(a, search_query)
        scored.append((score, a))
    top_articles = [
        a for s, a in nlargest(top_k, scored, key=lambda x: x[0])
        if s > 0
    ]

    if not top_articles and articles:
        # Fallback: most recent
        top_articles = sorted(
            articles,
            key=lambda at: at.get("published_at", at.get("date", "")),
            reverse=True
        )[:top_k]

    evidences = []
    for a in top_articles:
        evidences.append({
            "title": a.get("title", "Untitled"),
            "source": a.get("source") or a.get("publisher") or "unknown",
            "date": a.get("published_at") or a.get("date") or a.get("time_period"),
            "url": a.get("url") or a.get("link") or None,
            "snippet": (a.get("raw_text") or "")[:400],
            "sentiment_score": a.get("sentiment_score"),
            "emotion": a.get("emotion"),
        })

    # 6) Build counterspeech (Groq first, then fallback)
    counterspeech_text = None

    if groq_client and evidences:
        try:
            evidence_text = "\n\n".join(
                [
                    f"[{idx + 1}] {ev['title']} — {ev['snippet']}"
                    for idx, ev in enumerate(evidences)
                ]
            )

            prompt = f"""
You are a senior policy-oriented media analyst. A user has made the following public statement:

\"\"\"{statement}\"\"\"


You have access to the following recent reporting from credible news sources:

{evidence_text}

Your task is to produce a concise, professional counterspeech response that:

1. Provides a **fact-based, nuanced correction** to any exaggeration or misinformation in the statement.
2. Reflects the **overall picture** emerging from the evidence, especially regarding labour markets, automation, or structural change.
3. Uses a **measured and neutral tone**, similar to a government or multilateral policy brief.
4. Avoids bracketed citation markers like [1] or [2]. Instead, refer to evidence in natural language (e.g., “Recent coverage from a major business outlet notes…”, “Several industry analyses suggest…”).
5. Is written in **5–8 sentences**, aimed at a general but informed audience.
6. Emphasises **transition, adaptation, and policy responses** rather than alarmism.

Write only the final counterspeech text.
"""

            completion = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
            )
            counterspeech_text = completion.choices[0].message.content.strip()

        except Exception as e:
            print(f"[ERROR] Groq counterspeech generation error: {e}")
            counterspeech_text = None

    # Fallback if Groq not available or failed
    if not counterspeech_text:
        if evidences:
            first_snip = (
                evidences[0]["snippet"][:200]
                if evidences
                else "Recent reporting suggests a more nuanced picture."
            )
            lines = []
            lines.append(
                "Available reporting indicates a more nuanced labour-market transition "
                "rather than a simple story of technology replacing all jobs."
            )
            lines.append(
                f"For example, recent coverage notes that {first_snip} ..."
            )
            if len(evidences) > 1:
                lines.append(
                    "Additional analyses highlight both short-term dislocation and "
                    "longer-term job creation in adjacent or newly emerging roles."
                )
            lines.append(
                "From a policy perspective, the emphasis is on skills development, "
                "active labour-market measures, and organisational adaptation, "
                "rather than assuming a purely negative employment outcome."
            )
            counterspeech_text = "\n\n".join(lines)
        else:
            counterspeech_text = (
                "Current evidence generally suggests that automation and AI tend to "
                "reconfigure tasks within occupations rather than eliminate all jobs "
                "outright. While certain roles may face displacement in the short term, "
                "new opportunities often emerge in complementary areas, particularly "
                "where human judgment, oversight, and interaction remain essential. "
                "Most policy-focused analyses therefore stress reskilling, education, "
                "and targeted support for affected workers, rather than assuming a "
                "linear path towards widespread technological unemployment."
            )

    # 7) Build final response
    evidence_output = []
    for i, ev in enumerate(evidences, start=1):
        entry = {
            "index": i,
            "title": ev.get("title"),
            "source": ev.get("source"),
            "date": ev.get("date"),
            "url": ev.get("url"),
            "snippet": ev.get("snippet"),
        }
        evidence_output.append(entry)

    result = {
        "counterspeech": counterspeech_text,
        "evidences": evidence_output,
        "meta": {
            "search_query": search_query,
            "days_back": days_back,
            "found_articles": len(articles),
            "returned_evidences": len(evidence_output),
            "used_groq": bool(groq_client),
            "notes": (
                "If no evidences were returned, check SERPAPI key and "
                "news_fetcher implementation."
            ),
        },
    }
    return result
