import sys
import os
from langchain_core.tools import tool

# Ensure we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from analytics_manager import get_sentiment, get_emotion

@tool
def sentiment_tool(text: str):
    """
    Analyzes the sentiment and emotion of a given text.
    Returns the sentiment score (compound) and the dominant emotion.
    """
    print(f"--- ANALYZING SENTIMENT ---")
    
    try:
        sentiment = get_sentiment(text)
        emotion = get_emotion(text)
        
        return {
            "sentiment_score": sentiment,
            "emotion": emotion,
            "interpretation": "Positive" if sentiment > 0.05 else "Negative" if sentiment < -0.05 else "Neutral"
        }
            
    except Exception as e:
        return f"Error analyzing sentiment: {e}"