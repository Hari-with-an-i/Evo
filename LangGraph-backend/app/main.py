from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import BrainRequest, BrainResponse
from app.brain import brain_app

app = FastAPI(title="Evo Backend", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Allow frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/brain/invoke", response_model=BrainResponse)
async def invoke_brain(request: BrainRequest):
    """
    Invokes the LangGraph brain with a user message.
    """
    try:
        # The input to the graph is the state, specifically 'messages'
        # We wrap the user input in a HumanMessage. 
        # But LangGraph's add_messages reducer can handle dicts or strings too if configured, 
        # but better to provide the correct format.
        from langchain_core.messages import HumanMessage
        
        inputs = {"messages": [HumanMessage(content=request.input)]}
        
        # Invoke the graph
        result = brain_app.invoke(inputs)
        
        # Extract response from the last message in the conversation history
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1]
            final_response = last_message.content
        else:
            final_response = "No response generated."
        
        return BrainResponse(final_response=str(final_response))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
