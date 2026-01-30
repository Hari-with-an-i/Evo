from pydantic import BaseModel
from typing import Optional, Any

class BrainRequest(BaseModel):
    input: str
    thread_id: Optional[str] = None

class BrainResponse(BaseModel):
    final_response: str
    debug_info: Optional[Any] = None
