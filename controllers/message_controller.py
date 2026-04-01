from services.message_service import message_service

async def message_controller(user_id: str, message: str, conversationId: str):
    return await message_service(user_id, message, conversationId)