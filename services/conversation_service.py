from configs.database import db
from models.conversation_model import Conversation
from models.uploaded_file_model import UploadedFile
from datetime import datetime
from fastapi import UploadFile, File, APIRouter, HTTPException
import uuid
import os
import asyncio
import tempfile
from configs.supabase import supabase
from libs.safeFilename import safe_filename
from libs.ai.indexing import load_single_file, chunk_documents
from libs.ai.embedding import get_embedding_model

chatBox_collection = db["chat_boxes"]
upload_file = db["uploaded_files"]


async def create_chatbox(user_id: str):
    # Create a new chat box for the user
    chat_box = Conversation(userId=user_id,
                                 createdAt=datetime.utcnow(),
                                 updatedAt=datetime.utcnow()).dict( exclude_none=True   )
    result = await chatBox_collection.insert_one(chat_box)
    chat_box["id"] = str(result.inserted_id)
    chat_box.pop("_id", None)

    return chat_box


async def get_all_conversations_service(user_id: str):
    """Lấy tất cả conversations của user"""
    try:
        from bson import ObjectId
        conversations = await chatBox_collection.find({"userId": user_id}).sort("createdAt", -1).to_list(None)
        
        # Convert ObjectId to string
        for conv in conversations:
            conv["id"] = str(conv.pop("_id", ""))
        
        return conversations
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
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
        file_id_str = str(result.inserted_id)

        # Process embedding
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            def process_embedding(fpath):
                docs = load_single_file(fpath)
                if not docs:
                    return []
                chunks = chunk_documents(docs)
                embeddings_model = get_embedding_model()
                
                page_contents = [chunk.page_content for chunk in chunks]
                if not page_contents:
                    return []
                
                vectors = embeddings_model.embed_documents(page_contents)
                
                chunk_docs = []
                for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    page = chunk.metadata.get('page')
                    chunk_docs.append({
                        "fileId": file_id_str,
                        "chunkIndex": idx,
                        "content": chunk.page_content,
                        "embedding": vector,
                        "startPage": page + 1 if page is not None else None,
                        "endPage": page + 1 if page is not None else None
                    })
                return chunk_docs

            chunk_docs = await asyncio.to_thread(process_embedding, tmp_path)
            
            if chunk_docs:
                file_chunks_collection = db["file_chunks"]
                await file_chunks_collection.insert_many(chunk_docs)
                await upload_file.update_one({"_id": result.inserted_id}, {"$set": {"isProcessed": True}})
                
        except Exception as embed_err:
            print(f"Embedding error: {embed_err}")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        return {
            "id": file_id_str,
            "fileName": original_name,
            "storageUrl": public_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def delete_file_service(user_id: str, file_id: str):
    try:
        from bson import ObjectId
        # Tìm file
        file_to_delete = await upload_file.find_one({"_id": ObjectId(file_id), "userId": user_id})
        if not file_to_delete:
            raise HTTPException(status_code=404, detail="File không tồn tại hoặc bạn không có quyền truy cập")

        # Xóa file vật lý ở Supabase
        storage_path = file_to_delete.get("storagePath")
        if storage_path:
            try:
                supabase.storage.from_("files").remove([storage_path])
            except Exception as e:
                print(f"Lỗi khi xóa file trên Supabase: {e}")

        # Xóa chunks trong MongoDB
        file_chunks_collection = db["file_chunks"]
        await file_chunks_collection.delete_many({"fileId": file_id})

        # Xóa bản ghi UploadedFile
        await upload_file.delete_one({"_id": ObjectId(file_id)})

        return {
            "status": "success",
            "message": "Đã xóa file và toàn bộ chunks thành công"
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

async def delete_conversation_service(user_id: str, conversation_id: str):
    try:
        from bson import ObjectId
        # Kiểm tra sự tồn tại và quyền sở hữu conversation
        conv = await chatBox_collection.find_one({"_id": ObjectId(conversation_id), "userId": user_id})
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation không tồn tại hoặc bạn không có quyền truy cập")

        # Lấy tất cả file thuộc về conversation này
        files = await upload_file.find({"conversationId": conversation_id}).to_list(None)
        
        # Xóa các file (bao gồm supabase, file_chunks DB, upload DB)
        for f in files:
            try:
                await delete_file_service(user_id=user_id, file_id=str(f["_id"]))
            except Exception as fe:
                print(f"Lỗi khi xoá file {f['_id']} trong conversation: {fe}")

        # Xóa tất cả tin nhắn (Message)
        await db["messages"].delete_many({"conversationId": conversation_id})

        # Xóa conversation từ collection
        await chatBox_collection.delete_one({"_id": ObjectId(conversation_id)})

        return {
            "status": "success",
            "message": "Đã xóa toàn bộ dữ liệu của cuộc hội thoại thành công"
        }
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

async def get_all_files_service(user_id: str, conversation_id: str):
    """Retrieve all uploaded files belonging to a conversation."""
    try:
        files = await upload_file.find({"conversationId": conversation_id, "userId": user_id}).sort("createdAt", -1).to_list(None)
        # Convert ObjectId
        for f in files:
            f["id"] = str(f.pop("_id", ""))
            
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))