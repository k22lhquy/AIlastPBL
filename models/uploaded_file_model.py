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
    storagePath: str

    isProcessed: bool = False

    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None