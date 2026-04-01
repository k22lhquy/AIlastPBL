from fastapi import APIRouter, Depends
from middlewares.auth_middleware import get_current_user
from controllers.conversation_controller import create_conversation

router = APIRouter()

@router.get("/new-chat")
async def new_chat(user=Depends(get_current_user)):
    return await create_conversation(user["user_id"])