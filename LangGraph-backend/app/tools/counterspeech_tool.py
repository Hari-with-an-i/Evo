import asyncio
from langchain_core.tools import tool
from .analytics_manager import generate_counterspeech_with_evidence

@tool
def counterspeech_tool(statement: str):
    """
    Generates a counterspeech argument and finds relevant evidence for a given statement/misinformation.
    Use this when the user explicitly asks to "generate counter speech", "debunk this", or "provide an argument against" something.
    """
    print(f"--- GENERATING COUNTERSPEECH FOR: {statement} ---")
    
    try:
        # Use a helper to run async in a thread if needed, or just assume sync for now from the agent's perspective.
        
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
        return "System Error: Async Event Loop conflict. Please check logs."

    except Exception as e:
        return f"Error generating counterspeech: {e}"
