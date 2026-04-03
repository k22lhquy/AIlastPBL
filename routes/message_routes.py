from email import message

from fastapi import APIRouter, Depends, HTTPException
from controllers.message_controller import message_controller, get_messages_controller
from middlewares.auth_middleware import get_current_user
from pydantic import BaseModel
from libs.baseResponse import BaseResponse

class SendMessageRequest(BaseModel):
    message: str
    conversationId: str
    
router = APIRouter()

@router.post("/send_message")
async def send_message(user=Depends(get_current_user), request: SendMessageRequest = None):
    try:
        result = await message_controller(user_id=user["user_id"], message=request.message, conversationId=request.conversationId)
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/all_messages/{conversationId}")
async def get_messages(user=Depends(get_current_user), conversationId: str = None):
    try:
        result = await get_messages_controller(user_id=user["user_id"], conversationId=conversationId)
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))
