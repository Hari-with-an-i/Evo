from serpapi import GoogleSearch
from app.config import SERPAPI_KEY

def fetch_news_from_serpapi(keywords: str, num_results: int = 20, start_date: str = None, end_date: str = None):
    """
    Fetches news articles. Date range is now optional.
    """
    if not SERPAPI_KEY:
        print("[ERROR] SerpApi key not found in config.")
        return []

    print(f"[SEARCH] Calling SerpApi for '{keywords}'...")
    
    params = {
        "engine": "google",
        "q": keywords,
        "tbm": "nws",
        "num": num_results,
        "api_key": SERPAPI_KEY,
    }

    if start_date and end_date:
        print(f"   -> Applying date filter: {start_date} to {end_date}")
        params["tbs"] = f"cdr:1,cd_min:{start_date},cd_max:{end_date}"

    try:
        search = GoogleSearch(params)
        results_dict = search.get_dict()
        news_articles = results_dict.get("news_results")

        if not news_articles:
            print("[WARNING] No news articles found.")
            return []

        print(f"[SUCCESS] Successfully fetched {len(news_articles)} articles.")
        return news_articles

    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")
        return []
