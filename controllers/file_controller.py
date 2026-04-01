# controllers/file_controller.py
from services.file_service import (
    create_uploaded_file,
    get_user_files,
    get_file_by_id,
    get_conversation_files,
    delete_file
)
from fastapi import UploadFile
from typing import Optional

async def handle_upload_file(
    file: UploadFile,
    user_id: str,
    conversation_id: Optional[str] = None
):
    """Handle file upload"""
    return await create_uploaded_file(file, user_id, conversation_id)

async def handle_get_user_files(user_id: str, skip: int = 0, limit: int = 20):
    """Handle get user files"""
    return await get_user_files(user_id, skip, limit)

async def handle_get_file(file_id: str, user_id: str):
    """Handle get file by id"""
    return await get_file_by_id(file_id, user_id)

async def handle_get_conversation_files(conversation_id: str, user_id: str):
    """Handle get conversation files"""
    return await get_conversation_files(conversation_id, user_id)

async def handle_delete_file(file_id: str, user_id: str):
    """Handle delete file"""
    return await delete_file(file_id, user_id)