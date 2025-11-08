import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import re
from datetime import datetime, timedelta
from heapq import nlargest

# --- Local Analysis Tools ---
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from transformers import pipeline

# --- API Tools ---
from groq import Groq
from news_fetcher import fetch_news_from_serpapi
from config import GROQ_API_KEY

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
    # ... (This function is correct and remains the same)
    for article in articles:
        text = article.get("raw_text", "")
        article['sentiment_score'] = get_sentiment(text)
        article['emotion'] = get_emotion(text)
    print("✅ Text analysis complete.")
    return articles

def tool_fetch_time_series_data(keywords: str, time_period_days: int, granularity_days: int) -> list:
    print(f"🗓️ Fetching time-series data for '{keywords}'...")
    # ... (This function is correct and remains the same)
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
    
    for period, articles in grouped_articles.items():
        print(f"  -> Processing period starting {period} ({len(articles)} articles)")
        corpus = "\n\n---\n\n".join([f"Title: {a['title']}\n{a['raw_text']}" for a in articles])
        avg_sentiment = sum(a['sentiment_score'] for a in articles) / len(articles)
        
        narratives = "Could not determine narratives (Groq client not initialized)."
        if groq_client:
            # --- THIS IS THE FIX: Using Groq instead of Gemini ---
            narrative_prompt = f"Analyze the following news articles from a single time period. Identify and summarize the 2-3 dominant, distinct narratives or sub-plots. Be specific and concise.\n\nARTICLES:\n{corpus[:12000]}"
            try:
                chat_completion = groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": narrative_prompt}],
                    model="llama-3.3-70b-versatile" # Use a fast model for summarization
                )
                narratives = chat_completion.choices[0].message.content
            except Exception as e:
                print(f"❌ Groq narrative generation error: {e}")
                narratives = "Could not determine narratives for this period due to an API error."
        
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

    # --- THIS IS THE CORRECTED PROMPT ---
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
        print("✅ Full narrative report generated successfully by Groq.")
        return report
    except Exception as e:
        print(f"❌ Groq API Report Generation Error: {e}")
        return {"error": "Failed to generate report from Groq API.", "details": str(e)}
    
def _keyword_from_statement(statement: str) -> str:
    # Simple keyword extractor: picks noun-like words; keep it small and readable.
    # You can replace this with a more sophisticated extractor.
    words = re.findall(r"\b[a-zA-Z']{3,}\b", statement.lower())
    # remove common stopwords (small set)
    stop = {"the","and","for","that","this","with","from","are","was","have","has","but","not","you","your","they","their","it's","its","is","a","an","on","in","to","of"}
    keywords = [w for w in words if w not in stop]
    # join top few unique words
    uniq = []
    for w in keywords:
        if w not in uniq:
            uniq.append(w)
        if len(uniq) >= 6:
            break
    return " ".join(uniq) or statement[:80]

def _score_article_relevance(article: dict, query: str) -> float:
    # Very simple relevance: count occurrences in title + raw_text, weighted by recency
    text = (article.get("title","") + " " + article.get("raw_text","")).lower()
    qterms = [t for t in re.findall(r"\b[a-zA-Z']{3,}\b", query.lower()) if len(t) > 2]
    if not qterms:
        return 0.0
    count = sum(text.count(t) for t in qterms)
    # recency weight: newer articles get a small boost
    date_str = article.get("published_at") or article.get("date") or article.get("time_period")
    recency_weight = 1.0
    try:
        if date_str:
            # try ISO-ish parse
            dt = datetime.fromisoformat(date_str[:10])
            days_old = (datetime.now() - dt).days
            recency_weight = 1.0 / (1 + days_old/30)  # 1 -> 0.5 over 30 days
    except Exception:
        recency_weight = 1.0
    return count * recency_weight

def generate_counterspeech_with_evidence(statement: str,
                                         days_back: int = 30,
                                         top_k: int = 3,
                                         keywords: str | None = None) -> dict:
    """
    Produces a counterspeech (few short paragraphs) for `statement` and returns
    top_k news evidences supporting the counterspeech.
    Returns a dict: {"counterspeech": str, "evidences": [ {title,source,date,url,snippet} ], "meta": {...}}
    """
    # 1) Prepare keywords
    if keywords is None or not keywords.strip():
        search_query = _keyword_from_statement(statement)
    else:
        # Basic validation for user-supplied keywords:
        # - require at least 2 non-stopword tokens OR length >= 8 characters
        cleaned = " ".join([w for w in re.findall(r"\b[a-zA-Z']{3,}\b", keywords.lower())])
        if len(cleaned.split()) >= 2 or len(cleaned) >= 8:
            search_query = cleaned
        else:
            # provided keywords look too short/generic; fall back to auto-extraction
            print(f"⚠️ Ignoring weak user keywords '{keywords}'. Using auto-extracted query instead.")
            search_query = _keyword_from_statement(statement)

    # 2) Fetch recent articles (use existing helper)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    start_date_str = start_date.strftime("%m/%d/%Y")
    end_date_str = end_date.strftime("%m/%d/%Y")

    print(f"🔎 Searching news for: '{search_query}' from {start_date_str} to {end_date_str}")
    try:
        articles = fetch_news_from_serpapi(keywords=search_query, start_date=start_date_str, end_date=end_date_str)
    except Exception as e:
        print(f"❌ Error fetching news: {e}")
        articles = []

    # Ensure we have raw_text for scoring — light fallback: combine snippet/title
    for a in articles:
        if not a.get("raw_text") and a.get("snippet"):
            a["raw_text"] = a["snippet"]
        if not a.get("raw_text"):
            a["raw_text"] = a.get("title", "")

    # 3) Run quick text analytics (sentiment + emotion) to enrich articles
    try:
        articles = tool_run_text_analytics(articles)
    except Exception as e:
        print(f"⚠️ Text analytics failed: {e}")

    # 4) Score relevance and pick top_k
    scored = []
    for a in articles:
        score = _score_article_relevance(a, search_query)
        scored.append((score, a))
    top_articles = [a for s,a in nlargest(top_k, scored, key=lambda x: x[0]) if s > 0]
    # If none scored >0, fallback to most recent top_k
    if not top_articles and articles:
        top_articles = sorted(articles, key=lambda at: at.get("published_at", at.get("date","")), reverse=True)[:top_k]

    evidences = []
    for a in top_articles:
        evidences.append({
            "title": a.get("title","Untitled"),
            "source": a.get("source") or a.get("publisher") or a.get("org") or "unknown",
            "date": a.get("published_at") or a.get("date") or a.get("time_period"),
            "url": a.get("url") or a.get("link") or None,
            "snippet": (a.get("raw_text") or "")[:400],  # short snippet
            "sentiment_score": a.get("sentiment_score"),
            "emotion": a.get("emotion")
        })

    # 5) Build a prompt for Groq (if available)
    counterspeech_text = None
    if groq_client:
        prompt = f"""
You are a professional, calm, and respectful public communicator. Given a short user statement below, produce a concise counterspeech in **3 short paragraphs** (each paragraph 1-3 sentences). The counterspeech should be:
- factual, non-abusive, and non-confrontational,
- focused on correcting misinformation or providing a constructive alternative viewpoint,
- reference up to {len(evidences)} supporting news items by number (use [1], [2], ... inline) that will be provided after the statement.

USER STATEMENT:
\"\"\"{statement}\"\"\"

NEWS EVIDENCE (numbered):
"""
        for i, ev in enumerate(evidences, start=1):
            title = ev["title"]
            date = ev.get("date","")
            src = ev.get("source","")
            snippet = ev.get("snippet","").replace("\n"," ")
            url = ev.get("url") or ""
            prompt += f"\n[{i}] Title: {title}\nSource: {src}\nDate: {date}\nURL: {url}\nSnippet: {snippet[:400]}\n"

        prompt += """
OUTPUT FORMAT:
Return a JSON object only (no extra text) with exactly two keys:
- "counterspeech": a string with the 3 short paragraphs separated by blank lines.
- "citations": an array of objects, each with keys "index" (int), "title", "source", "date", "url", "snippet".

Be concise and ensure the counterspeech cites the evidence numbers inline where relevant (e.g., "Recent reporting [1] shows...").
"""
        try:
            resp = groq_client.chat.completions.create(
                messages=[{"role":"user","content":prompt}],
                model="llama-3.3-70b-versatile",
                response_format={"type":"json_object"}
            )
            resp_text = resp.choices[0].message.content
            # parse JSON
            parsed = json.loads(resp_text)
            counterspeech_text = parsed.get("counterspeech")
            # sometimes the model returns its own evidence formatting; prefer our evidences if needed
            citations = parsed.get("citations", evidences)
        except Exception as e:
            print(f"❌ Groq counterspeech generation error: {e}")
            counterspeech_text = None
            citations = evidences
    else:
        # Fallback: simple template-based counterspeech
        citations = evidences
        lines = []
        lines.append(f"I understand the concern raised in your statement. However, current reporting suggests a more nuanced picture: {citations[0]['snippet'][:200] if citations else 'Relevant reporting shows otherwise.'} [1].")
        if len(citations) > 1:
            lines.append(f"Additional coverage highlights other key facts and trends (see [2]).")
        else:
            lines.append("Independent reporting and analysis provide context that counters the claim.")
        lines.append("A constructive way forward is to verify claims against reliable sources, consider alternate explanations, and engage respectfully with differing viewpoints.")
        counterspeech_text = "\n\n".join(lines)

    # Format final evidence list to return (ensure only necessary fields)
    evidence_output = []
    for i, ev in enumerate(citations, start=1):
        # if citations came from model and are not full objects, fall back to our data
        if isinstance(ev, dict) and ev.get("title"):
            entry = {
                "index": i,
                "title": ev.get("title"),
                "source": ev.get("source"),
                "date": ev.get("date"),
                "url": ev.get("url"),
                "snippet": ev.get("snippet")
            }
        else:
            # fallback to earlier evidences list if model returned text
            if i-1 < len(evidences):
                e = evidences[i-1]
                entry = {
                    "index": i,
                    "title": e.get("title"),
                    "source": e.get("source"),
                    "date": e.get("date"),
                    "url": e.get("url"),
                    "snippet": e.get("snippet")
                }
            else:
                entry = {"index": i, "title": str(ev), "source": "", "date":"", "url":"", "snippet":""}
        evidence_output.append(entry)

    result = {
        "counterspeech": counterspeech_text,
        "evidences": evidence_output,
        "meta": {
            "search_query": search_query,
            "days_back": days_back,
            "found_articles": len(articles),
            "returned_evidences": len(evidence_output),
            "used_groq": bool(groq_client)
        }
    }
    return result
