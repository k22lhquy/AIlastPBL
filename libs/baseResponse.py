from pydantic import BaseModel
from typing import Any

class BaseResponse(BaseModel):
    success: bool
    data: Any
    message: str = ""