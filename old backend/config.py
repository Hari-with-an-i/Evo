import os
from dotenv import load_dotenv

# This line loads the .env file from the same directory
load_dotenv()

# Load the keys into variables
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEO4J_URI = "bolt://localhost:7687"  # Or your actual Neo4j connection URI
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Evo12345"