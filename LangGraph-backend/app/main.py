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
        inputs = {"messages": [request.input]}
        
        # Invoke the graph
        # Since the graph might have async tools (some are fake async via thread), 
        # but the graph itself is synchronous in definitions (unless we used async nodes everywhere),
        # we can use invoke. However, FastAPI is async, so better to thread it if it's blocking.
        # But for now, let's just call it directly.
        
        result = brain_app.invoke(inputs)
        
        final_response = result.get("final_response", "No response generated.")
        
        return BrainResponse(final_response=str(final_response))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
