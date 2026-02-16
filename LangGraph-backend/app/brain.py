from typing import Annotated, List
from typing_extensions import TypedDict

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# Import tools
from app.tools.scout_tool import scout_tool
from app.tools.time_fetcher import time_tool
from app.tools.source_filtering import source_tool
from app.tools.sentiment_score import sentiment_tool
from app.tools.generate_narrative_report import narrative_report_tool
from app.tools.counterspeech_tool import counterspeech_tool

# Initialize LLM
from app.config import GROQ_API_KEY

if not GROQ_API_KEY:
    print("WARNING: GROQ_API_KEY not found. Agent may fail.")

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0, api_key=GROQ_API_KEY)

# Define Tools
# We list all available tools so the agent can choose dynamically
tools = [
    scout_tool, 
    time_tool, 
    source_tool, 
    sentiment_tool, 
    narrative_report_tool, 
    counterspeech_tool
]

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

# Define State
class AgentState(TypedDict):
    # 'messages' is a list of message objects (HumanMessage, AIMessage, ToolMessage, etc.)
    # 'add_messages' ensures that new messages are appended to the existing history
    messages: Annotated[List, add_messages]

# System Prompt
SYSTEM_PROMPT = """You are an intelligent Misinformation Mitigation Assistant.
Your goal is to help users identify, analyze, and combat misinformation using a suite of advanced tools.

**Tool Usage Guidelines:**
1. **scout_tool**: Use this for general queries to get initial context, facts, and recent news snippets.
2. **time_tool**: Use this when the user asks for trends over a specific period (e.g., "last 24 hours", "past week").
3. **source_tool**: Use this when the user explicitly asks for information from *reliable* or *credible* sources only.
4. **counterspeech_tool**: Use this to generate arguments or debunk specific claims.
5. **narrative_report_tool**: Use this ONLY when the user asks for a full "report", "briefing", or comprehensive strategy.
6. **sentiment_tool**: Use this to analyze the sentiment of a specific text if needed.

**Strategy:**
- You are a **dynamic agent**. You can chain tools together.
- Example: If a user asks "How has the perception of AI changed in the last 24 hours?", you might first use `scout_tool` to understand the current context, and then `time_tool` to get the temporal data.
- Always answer the user's question directly based on the tool outputs.
"""

# Define Nodes
def agent_node(state: AgentState):
    print("--- AGENT THINKING ---")
    messages = state["messages"]
    
    # Prepend system message if it's the first turn or if we want to enforce it every time
    # Ideally, we put it at the start.
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    else:
        # Ensure the first message is always our system prompt (or at least consistent)
        pass 
        # In a persistent memory case, we might need to handle this differently, 
        # but for this request-response flow, we can just ensure the LLM sees the system prompt.
        
    # We can technically just pass the system prompt in the invoke call as a separate message list + state messages
    # But modifying state for clarity:
    
    response = llm_with_tools.invoke([SystemMessage(content=SYSTEM_PROMPT)] + state["messages"])
    return {"messages": [response]}

# Build Graph
builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")

# Conditional edge: If the agent calls a tool -> "tools" node. Else -> END.
builder.add_conditional_edges(
    "agent",
    tools_condition,
)

builder.add_edge("tools", "agent")

brain_app = builder.compile()
