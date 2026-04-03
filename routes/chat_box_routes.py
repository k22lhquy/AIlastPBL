from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from middlewares.auth_middleware import get_current_user
from controllers.conversation_controller import create_conversation, upload_file_controller, get_all_conversations_controller, delete_file_controller, delete_conversation_controller
from libs.baseResponse import BaseResponse

router = APIRouter()

@router.get("/new-chat")
async def new_chat(user=Depends(get_current_user)):
    try:
        result = await create_conversation(user["user_id"])
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.post("/upload-file")
async def upload_file(user=Depends(get_current_user), conversation_id: str = Form(None), file: UploadFile = File(...)):
    try:
        result = await upload_file_controller(user["user_id"], conversation_id, file)
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/all-conversations")
async def get_all_conversations(user=Depends(get_current_user)):
    try:
        result = await get_all_conversations_controller(user["user_id"])
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.delete("/delete-file/{file_id}")
async def delete_file(file_id: str, user=Depends(get_current_user)):
    try:
        result = await delete_file_controller(user["user_id"], file_id)
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.delete("/delete-conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, user=Depends(get_current_user)):
    try:
        result = await delete_conversation_controller(user["user_id"], conversation_id)
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))