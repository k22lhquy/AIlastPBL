from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from middlewares.auth_middleware import get_current_user
from controllers.conversation_controller import create_conversation, upload_file_controller, get_all_conversations_controller, delete_file_controller, delete_conversation_controller, get_all_files_controller, update_conversation_title_controller
from libs.baseResponse import BaseResponse
from pydantic import BaseModel

class RenameTitleRequest(BaseModel):
    title: str

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

@router.get("/files/{conversation_id}")
async def get_all_files(conversation_id: str, user=Depends(get_current_user)):
    try:
        result = await get_all_files_controller(user["user_id"], conversation_id)
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

@router.put("/rename/{conversation_id}")
async def rename_conversation(conversation_id: str, req: RenameTitleRequest, user=Depends(get_current_user)):
    try:
        result = await update_conversation_title_controller(user["user_id"], conversation_id, req.title)
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

class ImportFileRequest(BaseModel):
    file_id: str

@router.post("/import-file/{conversation_id}")
async def import_community_file(conversation_id: str, req: ImportFileRequest, user=Depends(get_current_user)):
    try:
        from configs.database import db
        from bson import ObjectId
        # Look up original file
        orig_file = await db["uploaded_files"].find_one({"_id": ObjectId(req.file_id)})
        if not orig_file:
            raise HTTPException(status_code=404, detail="File not found")
            
        # Duplicate file record for this specific chat
        new_file_doc = dict(orig_file)
        new_file_doc.pop("_id", None)
        new_file_doc["userId"] = user["user_id"]
        new_file_doc["conversationId"] = conversation_id
        new_file_doc["isCommunity"] = False
        new_file_doc["createdAt"] = __import__('datetime').datetime.utcnow()
        new_file_doc["updatedAt"] = __import__('datetime').datetime.utcnow()
        
        insert_res = await db["uploaded_files"].insert_one(new_file_doc)
        new_file_id_str = str(insert_res.inserted_id)
        
        # Quickly clone all embedded chunks so the RAG retains conversation separation
        chunks = await db["file_chunks"].find({"fileId": req.file_id}).to_list(None)
        if chunks:
            new_chunks = []
            for c in chunks:
                new_c = dict(c)
                new_c.pop("_id", None)
                new_c["fileId"] = new_file_id_str
                new_chunks.append(new_c)
            await db["file_chunks"].insert_many(new_chunks)
            
        return BaseResponse(success=True, data={"id": new_file_id_str}, message="File cloned successfully into workspace.")
        
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