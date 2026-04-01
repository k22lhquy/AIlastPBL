from services.conversation_service import create_chatbox

async def create_conversation(user_id: str):
    return await create_chatbox(user_id)