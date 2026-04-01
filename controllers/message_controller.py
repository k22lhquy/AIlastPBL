from services.message_service import message_service, get_messages_service

async def message_controller(user_id: str, message: str, conversationId: str):
    return await message_service(user_id, message, conversationId)

async def get_messages_controller(user_id: str, conversationId: str):
    return await get_messages_service(user_id, conversationId)