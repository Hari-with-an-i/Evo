import sys
import os
import json
from typing import TypedDict, Annotated, Literal, Optional, List
from pydantic import BaseModel, Field

# Ensure we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../Tools')))

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END

# Import our tools
from scout_tool import scout_tool
from time_fetcher import time_tool
from source_filtering import source_tool
from sentiment_score import sentiment_tool
from generate_narrative_report import narrative_report_tool
from counterspeech_tool import counterspeech_tool

# Initialize the LLM
from dotenv import load_dotenv
load_dotenv()
from config import GROQ_API_KEY

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found. Agent may fail.")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# --- 1. Define Structured Schema ---
class UserIntent(BaseModel):
    """Structured representation of the user's intent."""
    topic: str = Field(..., description="The main topic or subject of the user's query.")
    action_type: Literal["fetch_trend", "generate_report", "counter_speech", "general_query"] = Field(
        ..., description="The primary action to perform based on the user's request."
    )
    time_period_days: Optional[int] = Field(
        30, description="The number of days to analyze. Default to 30 if not specified. if 'last 24 hours', use 1."
    )
    reliable_sources_only: bool = Field(
        False, description="Whether to filter for reliable sources only."
    )
    specific_question: Optional[str] = Field(
        None, description="The specific question asked by the user, if applicable."
    )

# --- 2. Define Agent State ---
class AgentState(TypedDict):
    messages: List[Annotated[str, "The conversation history"]]
    user_intent: Optional[UserIntent]
    final_response: Optional[str]

# --- 3. Define Nodes ---

def brain_node(state: AgentState):
    """
    The Brain Node: Analyzes the user's request and populates the structured schema.
    """
    print("--- BRAIN NODE: ANALYZING INTENT ---")
    messages = state["messages"]
    last_message = messages[-1] if messages else ""
    
    # Use the LLM with structured output to populate UserIntent
    # Llama 3 via Groq supports with_structured_output (usually)
    # If not, we might need a fallback prompt, but let's try this first.
    
    structured_llm = llm.with_structured_output(UserIntent)
    
    system_prompt = """You are the intelligent Brain of a Misinformation Mitigation System. 
    Analyze the user's request and extract the structured intent.
    - If they ask for a report, briefing, or strategy, set action_type to 'generate_report'.
    - If they ask for trends or history, set action_type to 'fetch_trend'.
    - If they ask to debunk or argue, set action_type to 'counter_speech'.
    - Otherwise, use 'general_query'.
    - Extract reliable source requirements and time periods accurately.
    """
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}")
    ])
    
    chain = prompt | structured_llm
    try:
        intent = chain.invoke({"input": last_message})
        print(f"  Extracted Intent: {intent}")
        return {"user_intent": intent}
    except Exception as e:
        print(f"  Error extracting intent: {e}")
        # Fallback to a default intent if parsing fails
        return {"user_intent": UserIntent(topic="Unknown", action_type="general_query")}

def action_router(state: AgentState):
    """
    Routes to the appropriate node based on user_intent.
    """
    intent = state["user_intent"]
    if intent.action_type == "generate_report":
        return "report_node"
    elif intent.action_type == "fetch_trend":
        return "trend_node"
    elif intent.action_type == "counter_speech":
        return "counter_speech_node"
    else:
        return "general_node"

def report_node(state: AgentState):
    print("--- REPORT NODE ---")
    intent = state["user_intent"]
    # We pass the intent to verify the tool uses it, or just use the topic as per current tool def
    # The narrative_report_tool currently takes 'topic: str'
    
    print(f"  Generating report for {intent.topic}...")
    report_content = narrative_report_tool.invoke(intent.topic)
    
    return {"final_response": report_content}

def trend_node(state: AgentState):
    print("--- TREND NODE ---")
    intent = state["user_intent"]
    
    # Construct a refining query for the tool based on schema
    query = f"Perception trend of {intent.topic} in last {intent.time_period_days} days"
    if intent.reliable_sources_only:
        query += " from reliable sources"
        
    # time_tool basically runs a search similar to scout but focused on time.
    # We invoke it with the refined query.
    result = time_tool.invoke(query)
    return {"final_response": f"Trend Analysis for {intent.topic}:\n{result}"}

def counter_speech_node(state: AgentState):
    print("--- COUNTER SPEECH NODE ---")
    intent = state["user_intent"]
    result = counterspeech_tool.invoke(intent.topic)
    return {"final_response": f"Counter Speech Strategies:\n{result}"}

def general_node(state: AgentState):
    print("--- GENERAL NODE ---")
    intent = state["user_intent"]
    result = scout_tool.invoke(intent.topic)
    return {"final_response": result}

# --- 4. Build Graph ---
workflow = StateGraph(AgentState)

workflow.add_node("brain", brain_node)
workflow.add_node("report_node", report_node)
workflow.add_node("trend_node", trend_node)
workflow.add_node("counter_speech_node", counter_speech_node)
workflow.add_node("general_node", general_node)

workflow.add_edge(START, "brain")

workflow.add_conditional_edges(
    "brain",
    action_router,
    {
        "report_node": "report_node",
        "trend_node": "trend_node",
        "counter_speech_node": "counter_speech_node",
        "general_node": "general_node"
    }
)

workflow.add_edge("report_node", END)
workflow.add_edge("trend_node", END)
workflow.add_edge("counter_speech_node", END)
workflow.add_edge("general_node", END)

app = workflow.compile()

if __name__ == "__main__":
    print("--- STARTING BRAIN (Structured) ---")
    # Test queries
    queries = [
        "What is the perception trend of AI in the last 24 hours from reliable sources?",
        "Generate a report on Misinformation strategies",
        "How to counter deepfakes?"
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
        result = app.invoke({"messages": [q]})
        print(f"Result: {result.get('final_response')[:200]}...") # Truncated for display