from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Message(BaseModel):
    id: Optional[str] = None
    conversationId: str
    role: str   # "user" | "assistant"
    content: str
    timestamp: Optional[datetime] = None
    tokens: Optional[int] = None
    referencedFiles: Optional[List[str]] = []