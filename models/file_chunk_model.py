from pydantic import BaseModel
from typing import Optional, List

class FileChunk(BaseModel):
    id: Optional[str] = None
    fileId: str

    chunkIndex: int
    content: str

    embedding: Optional[List[float]] = None

    startPage: Optional[int] = None
    endPage: Optional[int] = None