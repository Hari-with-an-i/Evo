from langchain_core.tools import tool
# Import your existing logic functions here
# from your_project.search_engine import serp_api_fetch

@tool
def query_expansion(query: str):
    """
    Use this tool when the user's input is too brief, ambiguous, or lacks specific keywords. 
    It expands the query into a more detailed search string to improve retrieval accuracy. 
    If the initial search results are poor, this tool can be recalled to try a different expansion strategy.
    """
    print(f"🤖 Using LLM to extract keyword from: '{user_query}'")
    try:
        # Initialize the client from environment variable
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        prompt = (
            "You are an expert search query analyst. "
            "Analyze the following user query and extract the core, neutral topic or keyword phrase. "
            "The output should be a clean search term only, with no extra explanation. "
            f"QUERY: '{user_query}'"
        )
        # Using synchronous call as this function is synchronous
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt
        )
        keyword = response.text.strip()
        print(f"✅ Extracted Keyword: '{keyword}'")
        return keyword

    except Exception as e:
        print(f"❌ LLM Keyword Extraction Error: {e}")
        # Fallback to using the raw query if LLM fails
        return user_query
