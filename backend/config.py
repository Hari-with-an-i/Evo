import os
from dotenv import load_dotenv

# This line loads the .env file from the same directory
load_dotenv()

# Load the keys into variables
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")