from configs.database import db
from models.conversation_model import Conversation
from models.uploaded_file_model import UploadedFile
from datetime import datetime
from fastapi import UploadFile, File, APIRouter, HTTPException
import uuid
from configs.supabase import supabase
from libs.safeFilename import safe_filename

chatBox_collection = db["chat_boxes"]
upload_file = db["uploaded_files"]


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
    
# def safe_filename(filename: str):
#     filename = unicodedata.normalize("NFC", filename)
#     return re.sub(r'[^\w\-.]', '_', filename)
    
async def upload_file_service(user_id: str, conversation_id: str, file: UploadFile):
    try:
        content = await file.read()

        original_name = safe_filename(file.filename)

        file_ext = original_name.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"

        file_path = f"uploads/{user_id}/{file_name}"

        # upload supabase
        supabase.storage.from_("files").upload(
            file_path,
            content,
            {"content-type": file.content_type or "application/octet-stream"}
        )

        public_url = supabase.storage.from_("files").get_public_url(file_path)

        doc = {
            "userId": user_id,
            "conversationId": conversation_id,

            "fileName": original_name,
            "storagePath": file_path,
            "storageUrl": public_url,

            "fileType": file.content_type,
            "fileSize": len(content),

            "cloudProvider": "supabase",

            "isProcessed": False,

            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }

        result = await upload_file.insert_one(doc)

        return {
            "id": str(result.inserted_id),
            "fileName": original_name,
            "storageUrl": public_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))