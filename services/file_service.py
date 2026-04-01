# services/file_service.py
from configs.database import db
from models.uploaded_file_model import UploadedFile
from libs.file_utils import upload_to_firebase, delete_from_firebase
from fastapi import UploadFile, HTTPException
from bson import ObjectId
from datetime import datetime
from typing import List, Optional

uploaded_files_collection = db["uploaded_files"]

async def create_uploaded_file(
    file: UploadFile,
    user_id: str,
    conversation_id: Optional[str] = None
) -> dict:
    """Upload file và lưu metadata vào MongoDB"""
    
    try:
        # Upload to Firebase Storage
        storage_url, storage_path, file_size = await upload_to_firebase(
            file=file,
            user_id=user_id
        )
        
        # Create file document
        file_doc = UploadedFile(
            userId=user_id,
            conversationId=conversation_id,
            fileName=file.filename,
            originalName=file.filename,
            fileType=file.content_type,
            fileSize=file_size,
            storageUrl=storage_url,
            storagePath=storage_path,
            cloudProvider="firebase",
            isProcessed=False,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow()
        ).dict(exclude_none=True)
        
        # Remove 'id' field if present
        file_doc.pop('id', None)
        
        # Insert to MongoDB
        result = await uploaded_files_collection.insert_one(file_doc)
        file_doc["id"] = str(result.inserted_id)
        
        return file_doc
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo file: {str(e)}"
        )

async def get_user_files(
    user_id: str,
    skip: int = 0,
    limit: int = 20
) -> List[dict]:
    """Lấy danh sách file của user"""
    
    cursor = uploaded_files_collection.find({
        "userId": user_id
    }).sort("createdAt", -1).skip(skip).limit(limit)
    
    files = await cursor.to_list(length=limit)
    
    # Convert ObjectId to string
    for file in files:
        file["id"] = str(file.pop("_id"))
    
    return files

async def get_file_by_id(file_id: str, user_id: str) -> dict:
    """Lấy thông tin chi tiết 1 file"""
    
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID")
    
    file = await uploaded_files_collection.find_one({
        "_id": ObjectId(file_id),
        "userId": user_id
    })
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file["id"] = str(file.pop("_id"))
    return file

async def get_conversation_files(
    conversation_id: str,
    user_id: str
) -> List[dict]:
    """Lấy tất cả file trong 1 conversation"""
    
    cursor = uploaded_files_collection.find({
        "conversationId": conversation_id,
        "userId": user_id
    }).sort("createdAt", -1)
    
    files = await cursor.to_list(length=None)
    
    for file in files:
        file["id"] = str(file.pop("_id"))
    
    return files

async def delete_file(file_id: str, user_id: str) -> bool:
    """Xóa file"""
    
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID")
    
    # Find file
    file = await uploaded_files_collection.find_one({
        "_id": ObjectId(file_id),
        "userId": user_id
    })
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete from Firebase Storage
    await delete_from_firebase(file["storagePath"])
    
    # Delete from MongoDB
    result = await uploaded_files_collection.delete_one({
        "_id": ObjectId(file_id)
    })
    
    return result.deleted_count > 0

async def update_file_processing(
    file_id: str,
    extracted_text: Optional[str] = None,
    embeddings: Optional[List[float]] = None
) -> bool:
    """Update file processing status"""
    
    if not ObjectId.is_valid(file_id):
        raise HTTPException(status_code=400, detail="Invalid file ID")
    
    update_data = {
        "isProcessed": True,
        "updatedAt": datetime.utcnow()
    }
    
    if extracted_text:
        update_data["extractedText"] = extracted_text
    
    if embeddings:
        update_data["embeddings"] = embeddings
    
    result = await uploaded_files_collection.update_one(
        {"_id": ObjectId(file_id)},
        {"$set": update_data}
    )
    
    return result.modified_count > 0