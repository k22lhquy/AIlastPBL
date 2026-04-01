from email import message

from fastapi import APIRouter, Depends, HTTPException
from controllers.message_controller import message_controller
from middlewares.auth_middleware import get_current_user
from pydantic import BaseModel

class SendMessageRequest(BaseModel):
    message: str
    conversationId: str

router = APIRouter()

@router.post("/send_message")
async def send_message(user=Depends(get_current_user), request: SendMessageRequest = None):
    return await message_controller(user_id=user["user_id"], message=request.message, conversationId=request.conversationId)
