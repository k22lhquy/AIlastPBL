from fastapi import APIRouter, Depends, UploadFile, File, Form
from middlewares.auth_middleware import get_current_user
from controllers.conversation_controller import create_conversation, upload_file_controller, get_all_conversations_controller, delete_file_controller

router = APIRouter()

@router.get("/new-chat")
async def new_chat(user=Depends(get_current_user)):
    return await create_conversation(user["user_id"])

@router.post("/upload-file")
async def upload_file(user=Depends(get_current_user), conversation_id: str = Form(None), file: UploadFile = File(...)):
    return await upload_file_controller(user["user_id"], conversation_id, file)

@router.get("/all-conversations")
async def get_all_conversations(user=Depends(get_current_user)):
    return await get_all_conversations_controller(user["user_id"])

@router.delete("/delete-file/{file_id}")
async def delete_file(file_id: str, user=Depends(get_current_user)):
    return await delete_file_controller(user["user_id"], file_id)