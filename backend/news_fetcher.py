from serpapi import GoogleSearch
from config import SERPAPI_KEY # <-- Import the key from config

def fetch_news_from_serpapi(keywords: str, num_results: int = 20):
    """
    Fetches news articles. The API key is now handled by config.py.
    """
    if not SERPAPI_KEY:
        print("❌ SerpApi key not found in config.")
        return None

    print(f"📡 Calling SerpApi for keywords: '{keywords}'")
    
    params = {
        "engine": "google",
        "q": keywords,
        "tbm": "nws",
        "num": num_results,
        "api_key": SERPAPI_KEY, # Use the key imported from config
    }

    try:
        # ... (rest of the function is the same)
        search = GoogleSearch(params)
        results_dict = search.get_dict()
        news_articles = results_dict.get("news_results")

        if not news_articles:
            print("⚠️ No news articles found in the API response.")
            return None

        print(f"✅ Successfully fetched {len(news_articles)} articles.")
        return news_articles

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return None