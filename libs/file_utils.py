# libs/file_utils.py
import os
import uuid
from datetime import timedelta
from fastapi import UploadFile, HTTPException
from configs.firebase_config import get_storage_bucket

# Allowed file types
ALLOWED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'txt': 'text/plain',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc': 'application/msword',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def get_file_extension(filename: str) -> str:
    """Lấy extension từ filename"""
    return filename.split('.')[-1].lower() if '.' in filename else ''

def validate_file_extension(filename: str) -> bool:
    """Validate file extension"""
    ext = get_file_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{ext} không được hỗ trợ. Chỉ chấp nhận: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )
    return True

def validate_file_size(file_size: int) -> bool:
    """Validate file size"""
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File quá lớn. Kích thước tối đa: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    return True

async def upload_to_firebase(
    file: UploadFile,
    user_id: str,
    folder: str = "uploads"
) -> tuple[str, str, int]:
    """
    Upload file to Firebase Storage
    Returns: (storage_url, storage_path, file_size)
    """
    try:
        # Validate file extension
        validate_file_extension(file.filename)
        
        # Generate unique filename
        file_ext = get_file_extension(file.filename)
        unique_filename = f"{uuid.uuid4()}.{file_ext}"
        storage_path = f"{folder}/{user_id}/{unique_filename}"
        
        # Get Firebase Storage bucket
        bucket = get_storage_bucket()
        
        # Create blob
        blob = bucket.blob(storage_path)
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validate file size
        validate_file_size(file_size)
        
        # Upload to Firebase
        blob.upload_from_string(
            file_content,
            content_type=file.content_type or ALLOWED_EXTENSIONS.get(file_ext)
        )
        
        # Generate signed URL (URL có thời hạn 1 năm)
        storage_url = blob.generate_signed_url(
            expiration=timedelta(days=365),
            method='GET'
        )
        
        # Reset file pointer for potential reuse
        await file.seek(0)
        
        return storage_url, storage_path, file_size
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi upload file: {str(e)}"
        )

async def delete_from_firebase(storage_path: str) -> bool:
    """Delete file from Firebase Storage"""
    try:
        bucket = get_storage_bucket()
        blob = bucket.blob(storage_path)
        blob.delete()
        return True
    except Exception as e:
        print(f"Error deleting file: {str(e)}")
        return False

def get_file_info(file: UploadFile) -> dict:
    """Get file information"""
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size if hasattr(file, 'size') else 0
    }