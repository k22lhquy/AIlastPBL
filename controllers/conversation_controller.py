from fastapi import UploadFile

from services.conversation_service import create_chatbox, upload_file_service, get_all_conversations_service, delete_file_service, delete_conversation_service

async def create_conversation(user_id: str):
    return await create_chatbox(user_id)

async def upload_file_controller(user_id: str, conversation_id: str, file: UploadFile):
    return await upload_file_service(user_id=user_id, conversation_id=conversation_id, file=file)

async def get_all_conversations_controller(user_id: str):
    return await get_all_conversations_service(user_id)

async def delete_file_controller(user_id: str, file_id: str):
    return await delete_file_service(user_id=user_id, file_id=file_id)

async def delete_conversation_controller(user_id: str, conversation_id: str):
    return await delete_conversation_service(user_id=user_id, conversation_id=conversation_id)