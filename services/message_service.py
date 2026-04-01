from configs.database import db
from models.message_model import Message
from datetime import datetime

message_collection = db["messages"]

async def message_service(user_id: str, message: str, conversationId: str):
    if not message:
        raise ValueError("Message content is required")
    if message.strip() == "":
        raise ValueError("Message content cannot be empty")
    
    mess = Message(
        conversationId=conversationId,
        role="user",
        content=message,
        timestamp=datetime.utcnow()
    ).dict(exclude_none=True)
    
    result = await message_collection.insert_one(mess)
    return {
        "message": message,
        "conversationId": conversationId
    }

async def get_messages_service(user_id: str, conversationId: str):
    messages_cursor = message_collection.find({"conversationId": conversationId}).sort("timestamp", 1)
    messages = []
    async for message in messages_cursor:
        message["id"] = str(message["_id"])
        del message["_id"]
        messages.append(message)
    return messages
# chỉnh lại return có status code và message rõ ràng hơn, có thể trả về id của message mới tạo để client dễ dàng quản lý sau này.