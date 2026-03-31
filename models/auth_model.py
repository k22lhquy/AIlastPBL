from pydantic import BaseModel
from typing import Optional

class AuthAccount(BaseModel):
    id: Optional[str] = None
    userId: str
    username: str
    password: str   # nhớ: lưu password đã hash