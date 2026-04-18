from pydantic import BaseModel, ConfigDict
from typing import List, Optional
import datetime

class PostModel(BaseModel):
    userId: str
    username: str
    title: str
    description: str
    fileId: str
    fileName: str
    storageUrl: Optional[str] = None
    likes: List[str] = []
    reports: List[str] = []
    createdAt: datetime.datetime = datetime.datetime.utcnow()
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "userId": "123",
                "username": "user1",
                "title": "Machine Learning Notes",
                "description": "Notes for chapter 1",
                "fileId": "abc",
                "fileName": "notes.pdf"
            }
        }
    )
