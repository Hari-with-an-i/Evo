import os
import urllib.parse
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from database_manager import tool_save_analysis,tool_fetch_analysis
from dotenv import load_dotenv
from analysis_tool import tool_spacy_analysis

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
    'timesofindia.indiatimes.com'
}

app = FastAPI(title="News Analysis Agent")

class AnalysisRequest(BaseModel):
    query: str # The user's natural language query

# --- Agent Tools ---

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
            
        # Extract the domain name from the link to check against our list
        domain = urllib.parse.urlparse(link).netloc.replace('www.', '')

        # THE FILTERING STEP
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
                        "raw_text": article.text
                    })
            except Exception as e:
                print(f"  ❌ Failed to parse {link}: {e}")
        else:
            print(f"  👎 Skipping non-credible source: {domain}")
    
    print(f"🧹 Process complete. Stored raw text from {len(cleaned_articles)} credible articles.")
    return cleaned_articles



@app.post("/analyze-query")
async def analyze_query(request: AnalysisRequest):
    if not (SERPAPI_KEY and GOOGLE_API_KEY):
        raise HTTPException(status_code=500, detail="API keys are not configured correctly in config.py.")

    # --- AGENTIC WORKFLOW EXECUTION ---
    
    # Step 1: Extract Keyword
    search_keyword = await tool_extract_keyword(request.query)

    # Step 2: Fetch Articles
    raw_articles_list = fetch_news_from_serpapi(keywords=search_keyword)
    if not raw_articles_list:
        raise HTTPException(status_code=404, detail="No articles found for the extracted keyword.")

    # Step 3: Filter and Parse
    final_data = tool_filter_and_parse(raw_articles_list)
    if not final_data:
        raise HTTPException(status_code=404, detail="No credible articles could be parsed for this topic.")
        
    # --- CORRECTED LOGIC ---

    # 1. First, create the full response object
    response_data = {
        "status": "success",
        "user_query": request.query,
        "extracted_keyword": search_keyword,
        "credible_articles_found": len(final_data),
        "parsed_articles": final_data
    }

    # 2. Now, call the tool to save this object to the database
    document_id = tool_save_analysis(response_data)
    
    # 3. If saving was successful, add the new ID to the response
    if document_id:
        response_data["database_id"] = document_id
        
    # 4. Finally, return the complete response object at the very end
    return response_data

@app.get("/deep-analysis/{analysis_id}")
async def deep_analysis(analysis_id: str):
    """
    Retrieves a saved analysis and performs deep spaCy analysis on it.
    """
    # Step 1: Fetch the saved data from Firestore
    saved_data = tool_fetch_analysis(analysis_id)
    
    if not saved_data:
        raise HTTPException(status_code=404, detail="Analysis ID not found in the database.")
        
    cleaned_articles = saved_data.get("parsed_articles", [])
    
    # Step 2: Perform deep spaCy analysis on each article's raw text
    print(f"🔬 Performing deep analysis on {len(cleaned_articles)} articles...")
    enriched_articles = []
    for article in cleaned_articles:
        # The tool_spacy_analysis function is in your analysis_tool.py
        analysis_results = tool_spacy_analysis(article['raw_text'])
        article['analysis'] = analysis_results # Add the analysis results to the article object
        enriched_articles.append(article)
        
    # Replace the old articles with the newly enriched ones
    saved_data['parsed_articles'] = enriched_articles
    
    print("✅ Deep analysis complete.")
    return saved_data