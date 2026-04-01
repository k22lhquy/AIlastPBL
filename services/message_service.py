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
    
# chỉnh lại return có status code và message rõ ràng hơn, có thể trả về id của message mới tạo để client dễ dàng quản lý sau này.