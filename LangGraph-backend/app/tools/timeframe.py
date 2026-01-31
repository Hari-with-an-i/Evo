from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import date, timedelta
import requests
import logging
import sys
import time


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Thresholds
MIN_ARTICLES = 8            # Minimum relevant articles needed to stop
RELEVANCE_THRESHOLD = 0.35  # Per-article minimum score to count as "relevant"

# Timeframe steps: narrow → wide (find the TIGHTEST window that works)
TIMEFRAME_STEPS = [3, 6, 12, 18, 24, 36]  # months

# Rate limiting
REQUEST_DELAY = 1.5
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0

app = FastAPI(title="Dynamic Timeframe Agent")

class TimeframeRequest(BaseModel):
    query: str


def fetch_news(query, start_date, end_date, num=20):
    cd_min = start_date.strftime("%m/%d/%Y")
    cd_max = end_date.strftime("%m/%d/%Y")

    params = {
        "engine": "google",
        "q": query,
        "tbm": "nws",
        "num": num,
        "api_key": SERPAPI_API_KEY,
        "tbs": f"cdr:1,cd_min:{cd_min},cd_max:{cd_max}",
    }

    logger.info(f"      → Calling SerpAPI: {cd_min} to {cd_max}")

    for attempt in range(MAX_RETRIES):
        try:
            if attempt > 0:
                delay = REQUEST_DELAY * (RETRY_BACKOFF ** attempt)
                logger.info(f"      → Retry {attempt}/{MAX_RETRIES}, waiting {delay:.1f}s...")
                time.sleep(delay)
            else:
                time.sleep(REQUEST_DELAY)

            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            response.raise_for_status()
            return response.json().get("news_results", [])

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"      ⚠️ Rate limited (429), retrying...")
                continue
            logger.error(f"      ✗ HTTP error: {e}")
            return []
        except Exception as e:
            logger.error(f"      ✗ Error: {str(e)}")
            return []

    logger.error(f"      ✗ Failed after {MAX_RETRIES} retries")
    return []

# QUERY EXPANSION
def expand_query(query: str):
    base = query.strip()
    lower = base.lower()
    variants = [base]

    if any(w in lower for w in ['investigation', 'scandal', 'controversy']):
        variants.append(f"{base} updates")
    elif any(w in lower for w in ['death', 'died', 'killed']):
        pass  # specific enough
    elif any(w in lower for w in ['policy', 'law', 'election']):
        variants.append(f"{base} news")
    elif len(base.split()) <= 2:
        variants.append(f"{base} news")
    else:
        variants.append(f"{base} latest")

    logger.info(f"   📝 {len(variants)} query variant(s)")
    return variants

# PER-ARTICLE RELEVANCE SCORING
STOP_WORDS = {'the','a','an','in','on','at','to','for','of','and','or','is','was',
              'are','were','has','have','had','that','this','with'}

def score_article(query: str, keywords: list, article: dict) -> float:
    """
    Score a single article 0.0 → 1.0.
    Coverage: what % of query keywords appear in title+snippet.
    Position: title hits weighted 2x over snippet hits.
    Phrase bonus: +0.25 if exact query string appears in title.
    """
    title = article.get('title', '').lower()
    snippet = article.get('snippet', '').lower()

    if not keywords:
        return 0.0

    title_hits = sum(1 for kw in keywords if kw in title)
    snippet_hits = sum(1 for kw in keywords if kw in snippet)
    unique_hits = sum(1 for kw in keywords if kw in title or kw in snippet)

    if unique_hits == 0:
        return 0.0

    coverage = unique_hits / len(keywords)
    position = (title_hits * 2 + snippet_hits) / (len(keywords) * 3)
    score = (coverage * 0.6) + (position * 0.4)

    if query.lower() in title:
        score = min(1.0, score + 0.25)

    return round(score, 3)

# FILTER + SCORE ARTICLES
def filter_and_score(query: str, articles: list) -> list:
    """
    Score every article individually.
    Keep only those that meet RELEVANCE_THRESHOLD.
    This is the key gate — irrelevant articles are thrown away
    so they can't inflate counts or averages.
    """
    keywords = [w.lower() for w in query.split()
                if len(w) > 2 and w.lower() not in STOP_WORDS]

    for article in articles:
        article["_relevance_score"] = score_article(query, keywords, article)

    # Sort best-first
    articles.sort(key=lambda a: a["_relevance_score"], reverse=True)

    relevant = [a for a in articles if a["_relevance_score"] >= RELEVANCE_THRESHOLD]
    irrelevant_count = len(articles) - len(relevant)

    logger.info(f"      → Scored: {len(relevant)} relevant, {irrelevant_count} irrelevant (threshold: {RELEVANCE_THRESHOLD})")
    if relevant:
        logger.info(f"      → Top scores: {[a['_relevance_score'] for a in relevant[:5]]}")

    return relevant

# AGENT CORE — NARROW → WIDE, STOP AT TIGHTEST WINDOW

def dynamic_timeframe_agent(query: str):
    """
    Start with the narrowest window (3 months) and expand outward.
    At each step, fetch articles and FILTER to only relevant ones.
    Stop the moment we have enough relevant articles.

    This guarantees the returned timeframe is the tightest possible
    window that contains sufficient relevant content.
    """
    today = date.today()
    best_result = None

    logger.info("=" * 80)
    logger.info(f"🔍 Agent started | Query: '{query}'")
    logger.info(f"📊 Strategy: narrow → wide | Steps: {TIMEFRAME_STEPS} months")
    logger.info(f"🎯 Goal: find tightest window with ≥{MIN_ARTICLES} relevant articles")
    logger.info("=" * 80)

    for iteration, months in enumerate(TIMEFRAME_STEPS, start=1):
        start_date = today - timedelta(days=months * 30)
        end_date = today

        logger.info("")
        logger.info(f"{'─' * 80}")
        logger.info(f"📅 Iteration {iteration}/{len(TIMEFRAME_STEPS)} | {months} months | {start_date} → {end_date}")
        logger.info(f"{'─' * 80}")

        # --- Fetch raw articles ---
        raw_articles = []
        for q in expand_query(query):
            logger.info(f"   🔎 Variant: '{q}'")
            fetched = fetch_news(q, start_date, end_date)
            logger.info(f"      ✓ {len(fetched)} fetched")
            raw_articles.extend(fetched)

        # Deduplicate by link
        seen = {}
        for a in raw_articles:
            link = a.get("link")
            if link:
                seen[link] = a
        raw_articles = list(seen.values())
        logger.info(f"   🔗 {len(raw_articles)} unique after dedup")

        # --- Score and filter: only keep articles that are actually relevant ---
        relevant_articles = filter_and_score(query, raw_articles)
        relevant_count = len(relevant_articles)

        avg_relevance = round(
            sum(a["_relevance_score"] for a in relevant_articles) / relevant_count, 2
        ) if relevant_count > 0 else 0.0

        logger.info("")
        logger.info(f"📊 Relevant: {relevant_count} | Avg relevance: {avg_relevance}")

        current_result = {
            "start_date": start_date,
            "end_date": end_date,
            "lookback_months": months,
            "article_count": relevant_count,
            "avg_relevance": avg_relevance,
            "iterations": iteration,
            "articles": relevant_articles,
        }

        # Always track the best we've seen
        if not best_result or relevant_count > best_result["article_count"]:
            best_result = current_result

        # ✅ STOP — tightest window with enough relevant articles
        if relevant_count >= MIN_ARTICLES:
            logger.info("")
            logger.info(f"✅ OPTIMAL WINDOW FOUND!")
            logger.info(f"   ✓ {relevant_count} relevant articles (need ≥{MIN_ARTICLES})")
            logger.info(f"   ✓ Avg relevance: {avg_relevance}")
            logger.info(f"   ✓ Timeframe: {months} months")
            logger.info("=" * 80)
            return current_result

        logger.info(f"   ⏩ {relevant_count}/{MIN_ARTICLES} relevant. Expanding...")

    # Exhausted all steps
    logger.info("")
    logger.info("=" * 80)
    logger.warning(
        f"⚠️ No window reached {MIN_ARTICLES} relevant articles. "
        f"Returning best: {best_result['article_count']} articles, {best_result['lookback_months']} months."
    )
    logger.info("=" * 80)
    return best_result

# API ENDPOINT
@app.post("/agent/dynamic-timeframe")
def get_timeframe(request: TimeframeRequest):
    try:
        logger.info("")
        logger.info("=" * 80)
        logger.info(f"📥 INCOMING REQUEST | Query: '{request.query}'")
        logger.info("=" * 80)

        result = dynamic_timeframe_agent(request.query)

        if not result:
            return {
                "status": "success",
                "query": request.query,
                "start_date": None,
                "end_date": None,
                "lookback_months": 0,
                "article_count": 0,
                "avg_relevance": 0,
                "iterations": 0,
                "articles_preview": [],
            }

        logger.info("")
        logger.info(f"✅ DONE | {result['start_date']} → {result['end_date']} | {result['article_count']} articles | {result['lookback_months']} months")
        logger.info("=" * 80)

        # Clean up internal score field for response, expose as relevance_score
        preview = []
        for a in result["articles"][:5]:
            clean = {k: v for k, v in a.items() if k != "_relevance_score"}
            clean["relevance_score"] = a.get("_relevance_score", 0)
            preview.append(clean)

        return {
            "status": "success",
            "query": request.query,
            "start_date": result["start_date"],
            "end_date": result["end_date"],
            "lookback_months": result["lookback_months"],
            "article_count": result["article_count"],
            "avg_relevance": result["avg_relevance"],
            "iterations": result["iterations"],
            "articles_preview": preview,
        }

    except Exception as e:
        logger.exception("❌ AGENT FAILED")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 80)
    logger.info("🚀 Dynamic Timeframe Agent started")
    logger.info(f"   Timeframe steps: {TIMEFRAME_STEPS} months")
    logger.info(f"   Min relevant articles: {MIN_ARTICLES}")
    logger.info(f"   Per-article relevance threshold: {RELEVANCE_THRESHOLD}")
    logger.info("=" * 80)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")