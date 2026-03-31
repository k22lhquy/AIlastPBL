from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UploadedFile(BaseModel):
    id: Optional[str] = None
    userId: str
    conversationId: Optional[str] = None

    fileName: str
    fileType: str
    fileSize: int

    storageUrl: str
    cloudProvider: Optional[str] = None

    extractedText: Optional[str] = None
    isProcessed: bool = False

    embeddings: Optional[List[float]] = None

    createdAt: Optional[datetime] = None