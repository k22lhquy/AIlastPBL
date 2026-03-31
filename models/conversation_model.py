from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Conversation(BaseModel):
    id: Optional[str] = None
    userId: str
    title: Optional[str] = None
    messageCount: int = 0
    isArchived: bool = False
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None