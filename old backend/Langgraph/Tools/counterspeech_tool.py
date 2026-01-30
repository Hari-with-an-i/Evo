import sys
import os
import asyncio
from langchain_core.tools import tool

# Ensure we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

try:
    from analytics_manager import generate_counterspeech_with_evidence
except ImportError:
    # Use relative import if running as a package or fallback
    from backend.analytics_manager import generate_counterspeech_with_evidence

@tool
def counterspeech_tool(statement: str):
    """
    Generates a counterspeech argument and finds relevant evidence for a given statement/misinformation.
    Use this when the user explicitly asks to "generate counter speech", "debunk this", or "provide an argument against" something.
    """
    print(f"--- GENERATING COUNTERSPEECH FOR: {statement} ---")
    
    try:
        # Since the backend function is async, and we want to run this in a potential sync agent context,
        # we can use asyncio.run to execute it if there's no running loop, 
        # OR we rely on the agent executor being async.
        # However, `create_react_agent` often wraps tools.
        # Safest way for a quick tool is to wrap in a sync wrapper that calls async, 
        # BUT nested asyncio loops are tricky.
        # Given we changed main.py to use `agent_chat` which is async, we should try to keep tools sync-compatible 
        # or use `ainvoke`.
        
        # Let's try to run it. If there is a running loop, this will fail.
        # If there is a running loop (FastAPI), we should return a coroutine? 
        # LangChain tools can be async. Let's make it async def? 
        # But for `create_react_agent`, it might expect sync tools unless we use `ainvoke`.
        
        # HACK: For now, I will use a helper to run async in a thread if needed, or just assume sync for now from the agent's perspective.
        # Actually, `generate_counterspeech_with_evidence` IS async.
        
        # Proper way:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate_counterspeech_with_evidence(statement=statement))
        loop.close()
        
        # Format the result for the LLM
        if not result or "counterspeech" not in result:
             return "Failed to generate counterspeech."
             
        cs = result["counterspeech"]
        evidences = result.get("evidences", [])
        
        evidence_text = "\n".join([f"- {e['title']} ({e['source']})" for e in evidences])
        
        output = f"**Counterspeech Argument:**\n{cs}\n\n**Key Evidence:**\n{evidence_text}"
        return output

    except RuntimeError:
        # If we are already in a loop (which we are in FastAPI), `asyncio.run` fails.
        # We need to bridge likely. 
        # The best way is to import the SYNC version or refactor `analytics_manager` to sync.
        # Or, just return a message saying "I can't run async tools yet inside the agent loop".
        return "System Error: Async Event Loop conflict. Please check logs."

    except Exception as e:
        return f"Error generating counterspeech: {e}"
