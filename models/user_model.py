from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: Optional[str] = None
    email: EmailStr
    name: str
    avatar: Optional[str] = None
    createdAt: Optional[datetime] = None
    lastActive: Optional[datetime] = None