import datetime
from typing import List, Optional
from pydantic import BaseModel

class QuestionModel(BaseModel):
    user_id: str
    body: str
    tags: List[str] = []
    created_at: datetime.datetime = datetime.datetime.utcnow()

class AnswerModel(BaseModel):
    question_id: str
    user_id: str
    body: str
    image_url: Optional[str] = None
    likes: List[str] = []
    created_at: datetime.datetime = datetime.datetime.utcnow()
