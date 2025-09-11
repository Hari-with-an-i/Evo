from serpapi import GoogleSearch
from config import SERPAPI_KEY

# The fix is in this function definition line
def fetch_news_from_serpapi(keywords: str, num_results: int = 20, start_date: str = None, end_date: str = None):
    """
    Fetches news articles. Date range is now optional.
    """
    if not SERPAPI_KEY:
        print("❌ SerpApi key not found in config.")
        # Return an empty list to prevent crashes in the calling code
        return []

    print(f"📡 Calling SerpApi for '{keywords}'...")
    
    params = {
        "engine": "google",
        "q": keywords,
        "tbm": "nws",
        "num": num_results,
        "api_key": SERPAPI_KEY,
    }

    # This 'if' block now correctly handles the optional dates.
    # If they are None, this block is skipped.
    if start_date and end_date:
        print(f"   -> Applying date filter: {start_date} to {end_date}")
        params["tbs"] = f"cdr:1,cd_min:{start_date},cd_max:{end_date}"

    try:
        search = GoogleSearch(params)
        results_dict = search.get_dict()
        news_articles = results_dict.get("news_results")

        if not news_articles:
            print("⚠️ No news articles found.")
            return []

        print(f"✅ Successfully fetched {len(news_articles)} articles.")
        return news_articles

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return []