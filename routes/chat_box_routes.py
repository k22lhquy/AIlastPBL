# routes/chat_box_routes.py
from fastapi import APIRouter, Depends, File, UploadFile, Form
from typing import Optional
from middlewares.auth_middleware import get_current_user
from controllers.conversation_controller import create_conversation
from controllers.file_controller import (
    handle_upload_file,
    handle_get_user_files,
    handle_get_file,
    handle_get_conversation_files,
    handle_delete_file
)

router = APIRouter()

@router.get("/new-chat")
async def new_chat(user=Depends(get_current_user)):
    return await create_conversation(user["user_id"])

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    user=Depends(get_current_user)
):
    """
    Upload file lên Firebase Storage
    
    - **file**: File cần upload (pdf, txt, docx, doc, jpg, png)
    - **conversation_id**: ID của conversation (optional)
    """
    result = await handle_upload_file(
        file=file,
        user_id=user["user_id"],
        conversation_id=conversation_id
    )
    
    return {
        "message": "File uploaded successfully",
        "data": result
    }

@router.get("/files")
async def get_files(
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user)
):
    """Lấy danh sách files của user"""
    files = await handle_get_user_files(
        user_id=user["user_id"],
        skip=skip,
        limit=limit
    )
    
    return {
        "message": "Files retrieved successfully",
        "data": files,
        "total": len(files)
    }

@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    user=Depends(get_current_user)
):
    """Lấy thông tin chi tiết 1 file"""
    file = await handle_get_file(
        file_id=file_id,
        user_id=user["user_id"]
    )
    
    return {
        "message": "File retrieved successfully",
        "data": file
    }

@router.get("/conversations/{conversation_id}/files")
async def get_conversation_files(
    conversation_id: str,
    user=Depends(get_current_user)
):
    """Lấy tất cả files trong 1 conversation"""
    files = await handle_get_conversation_files(
        conversation_id=conversation_id,
        user_id=user["user_id"]
    )
    
    return {
        "message": "Files retrieved successfully",
        "data": files,
        "total": len(files)
    }

@router.delete("/files/{file_id}")
async def delete_file_route(
    file_id: str,
    user=Depends(get_current_user)
):
    """Xóa file"""
    result = await handle_delete_file(
        file_id=file_id,
        user_id=user["user_id"]
    )
    
    return {
        "message": "File deleted successfully",
        "deleted": result
    }