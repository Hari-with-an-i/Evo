import sys
import os
from dotenv import load_dotenv

# Ensure we can import from app
sys.path.append(os.getcwd())

load_dotenv()

try:
    from app.brain import brain_app
    from langchain_core.messages import HumanMessage
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def test_query(query):
    print(f"\n\n>>> Testing Query: {query}")
    initial_state = {"messages": [HumanMessage(content=query)]}
    
    try:
        # We use invoke to get the final result
        result = brain_app.invoke(initial_state)
        
        print("--- Execution Trace ---")
        for msg in result["messages"]:
            content_preview = str(msg.content)[:200].replace('\n', ' ')
            print(f"[{msg.type.upper()}]: {content_preview}...")
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                 print(f"  [TOOL CALLS]: {msg.tool_calls}")
            
    except Exception as e:
        print(f"Execution Error: {e}")

if __name__ == "__main__":
    print("Starting Brain Dynamic Tests...")
    
    # 1. Simple fetch (Scout)
    test_query("What is the latest news on AI regulation?")
    
    # 2. Time sensitive (Time Tool)
    test_query("What is the perception trend of AI in the last 7 days?")
    
    # 3. Counter speech
    test_query("Debunk the claim that vaccines cause magnetism.")
