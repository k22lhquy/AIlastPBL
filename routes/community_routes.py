from fastapi import APIRouter, Depends, HTTPException, Form, UploadFile, File
import uuid
import tempfile
import os
import asyncio

from middlewares.auth_middleware import get_current_user, get_active_user
from controllers.community_controller import create_post_controller, get_all_posts_controller, toggle_like_controller, report_post_controller
from libs.baseResponse import BaseResponse
from pydantic import BaseModel
from typing import Optional
from configs.supabase import supabase
from libs.safeFilename import safe_filename
from libs.ai.indexing import load_single_file, chunk_documents
from libs.ai.embedding import get_embedding_model
from configs.database import db

router = APIRouter()

class CreatePostRequest(BaseModel):
    title: str
    description: str
    file_id: str
    file_name: str
    storage_url: Optional[str] = None
    tags: list[str] = []

class ReportRequest(BaseModel):
    reason: str

@router.post("/")
async def create_post(request: CreatePostRequest, user=Depends(get_active_user)):
    try:
        res = await create_post_controller(user, request)
        return BaseResponse(success=True, data=res, message="Post created")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/")
async def get_all_posts():
    try:
        res = await get_all_posts_controller()
        return BaseResponse(success=True, data=res, message="Posts retrieved")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/search/query")
async def search_posts(q: str, user=Depends(get_current_user)):
    try:
        import re
        escaped = re.escape(q)
        pattern = f".*{escaped}.*"
        query = {"$or": [
            {"title": {"$regex": pattern, "$options": "i"}},
            {"description": {"$regex": pattern, "$options": "i"}},
            {"tags": {"$regex": pattern, "$options": "i"}}
        ]}
        posts = await db["posts"].find(query).limit(50).to_list(50)
        result = [{
            "id": str(p["_id"]),
            "title": p.get("title", ""),
            "description": p.get("description", ""),
            "username": p.get("username", ""),
            "userId": p.get("userId", ""),
            "fileName": p.get("fileName", ""),
            "createdAt": p.get("createdAt", "").isoformat() if hasattr(p.get("createdAt", ""), "isoformat") else str(p.get("createdAt", "")),
            "likes": p.get("likes") if isinstance(p.get("likes"), list) else [],
            "tags": p.get("tags") if isinstance(p.get("tags"), list) else []
        } for p in posts]
        return BaseResponse(success=True, data=result, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.post("/{post_id}/like")
async def toggle_like(post_id: str, user=Depends(get_current_user)):
    try:
        res = await toggle_like_controller(user, post_id)
        return BaseResponse(success=True, data=res, message="Like toggled")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.post("/{post_id}/report")
async def report_post(post_id: str, request: ReportRequest, user=Depends(get_current_user)):
    try:
        res = await report_post_controller(user, post_id, request.reason)
        return BaseResponse(success=True, data=res, message="Reported")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/me/posts")
async def get_my_posts(user=Depends(get_current_user)):
    try:
        from controllers.community_controller import get_user_posts_controller
        res = await get_user_posts_controller(user)
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, user=Depends(get_current_user)):
    try:
        from controllers.community_controller import delete_post_controller
        res = await delete_post_controller(user, post_id)
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

class PreviewByIdRequest(BaseModel):
    file_id: str

@router.post("/posts/preview-chunks")
async def preview_by_file_id(req: PreviewByIdRequest):
    """Read file content directly from MongoDB file_chunks - avoids Supabase URL 400 errors."""
    try:
        file_id = req.file_id.strip()
        if not file_id:
            return BaseResponse(success=False, data=None, message="file_id không hợp lệ")
        
        chunks = await db["file_chunks"].find(
            {"fileId": file_id},
            {"content": 1, "chunkIndex": 1, "_id": 0}
        ).sort("chunkIndex", 1).to_list(None)
        
        if not chunks:
            return BaseResponse(success=False, data=None, message="Không tìm thấy nội dung tài liệu. File có thể chưa được xử lý.")
        
        content = "\n\n".join(c["content"] for c in chunks if c.get("content"))
        return BaseResponse(success=True, data=content, message="Success")
    except Exception as e:
        print(f"[preview_by_file_id] error: {e}")
        return BaseResponse(success=False, data=None, message=str(e))


@router.post("/upload")

async def upload_community_file(user=Depends(get_active_user), file: UploadFile = File(...)):
    try:
        content = await file.read()
        original_name = safe_filename(file.filename)
        file_ext = original_name.split('.')[-1]
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = f"community/{file_name}"

        # upload supabase
        content_type = file.content_type or "application/octet-stream"
        if content_type.startswith("text/"):
            content_type += "; charset=utf-8"

        supabase.storage.from_("files").upload(
            file_path,
            content,
            {"content-type": content_type}
        )
        public_url = supabase.storage.from_("files").get_public_url(file_path)

        doc = {
            "userId": user["user_id"],
            "fileName": original_name,
            "storagePath": file_path,
            "storageUrl": public_url,
            "fileType": file.content_type,
            "fileSize": len(content),
            "cloudProvider": "supabase",
            "isProcessed": False,
            "isCommunity": True,
            "createdAt": __import__('datetime').datetime.utcnow(),
            "updatedAt": __import__('datetime').datetime.utcnow()
        }

        upload_col = db["uploaded_files"]
        result = await upload_col.insert_one(doc)
        file_id_str = str(result.inserted_id)

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            def process_embedding(fpath):
                docs = load_single_file(fpath)
                if not docs: return []
                chunks = chunk_documents(docs)
                embeddings_model = get_embedding_model()
                page_contents = [chunk.page_content for chunk in chunks]
                if not page_contents: return []
                vectors = embeddings_model.embed_documents(page_contents)
                
                chunk_docs = []
                for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                    page = chunk.metadata.get('page')
                    chunk_docs.append({
                        "fileId": file_id_str,
                        "chunkIndex": idx,
                        "content": chunk.page_content,
                        "embedding": vector,
                        "isCommunity": True,
                        "startPage": page + 1 if page is not None else None,
                        "endPage": page + 1 if page is not None else None
                    })
                return chunk_docs

            chunk_docs = await asyncio.to_thread(process_embedding, tmp_path)
            
            if chunk_docs:
                await db["file_chunks"].insert_many(chunk_docs)
                await upload_col.update_one({"_id": result.inserted_id}, {"$set": {"isProcessed": True}})
                
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

        return BaseResponse(success=True, data={
            "id": file_id_str,
            "fileName": original_name,
            "storageUrl": public_url
        }, message="Community file embedded successfully")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))
