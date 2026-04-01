from configs.database import db
from models.conversation_model import Conversation
import datetime

chatBox_collection = db["chat_boxes"]


async def create_chatbox(user_id: str):
    # Create a new chat box for the user
    chat_box = Conversation(userId=user_id,
                                 createdAt=datetime.datetime.utcnow(),
                                 updatedAt=datetime.datetime.utcnow()).dict( exclude_none=True   )
    await chatBox_collection.insert_one(chat_box)

    return {
        "message": "Conversation created",
        "user_id": user_id
    }