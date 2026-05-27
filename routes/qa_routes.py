from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel
import uuid

from middlewares.auth_middleware import get_current_user
from controllers.qa_controller import (
    create_question_controller, get_all_questions_controller,
    get_question_controller, create_answer_controller,
    get_answers_controller, like_answer_controller
)
from libs.baseResponse import BaseResponse
from configs.supabase import supabase

router = APIRouter()

class CreateQuestionRequest(BaseModel):
    body: str
    tags: List[str] = []

class ReportRequest(BaseModel):
    reason: str

# ── Questions ─────────────────────────────────────────────────────────────────

@router.post("/questions")
async def create_question(request: CreateQuestionRequest, user=Depends(get_current_user)):
    try:
        res = await create_question_controller(user, request.body, request.tags)
        return BaseResponse(success=True, data={"id": res}, message="Question created")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/questions")
async def list_questions():
    try:
        res = await get_all_questions_controller()
        return BaseResponse(success=True, data=res, message="OK")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/search/query")
async def search_questions(q: str, user=Depends(get_current_user)):
    try:
        from configs.database import db
        import re
        escaped = re.escape(q)
        pattern = f".*{escaped}.*"
        query = {"$or": [
            {"body": {"$regex": pattern, "$options": "i"}},
            {"tags": {"$elemMatch": {"$regex": pattern, "$options": "i"}}}
        ]}
        questions = await db["questions"].find(query).limit(50).to_list(100)
        result = [{
            "id": str(q_doc["_id"]),
            "body": q_doc.get("body", ""),
            "username": q_doc.get("username", ""),
            "user_id": q_doc.get("user_id", ""),
            "tags": q_doc.get("tags", []),
            "answer_count": q_doc.get("answer_count", 0),
            "created_at": q_doc.get("created_at", "").isoformat() if hasattr(q_doc.get("created_at", ""), "isoformat") else str(q_doc.get("created_at", ""))
        } for q_doc in questions]
        return BaseResponse(success=True, data=result, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/questions/{question_id}")
async def get_question(question_id: str):
    try:
        res = await get_question_controller(question_id)
        if not res:
            return BaseResponse(success=False, data=None, message="Not found")
        return BaseResponse(success=True, data=res, message="OK")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.post("/questions/{question_id}/report")
async def report_question(question_id: str, req: ReportRequest, user=Depends(get_current_user)):
    try:
        from services.qa_service import report_question_service
        user_id = user["user_id"]
        await report_question_service(question_id, user_id, req.reason)
        return BaseResponse(success=True, data=None, message="Reported")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/me/questions")
async def get_my_questions(user=Depends(get_current_user)):
    try:
        from controllers.qa_controller import get_user_questions_controller
        res = await get_user_questions_controller(user)
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.delete("/questions/{question_id}")
async def delete_question(question_id: str, user=Depends(get_current_user)):
    try:
        from controllers.qa_controller import delete_question_controller
        res = await delete_question_controller(user, question_id)
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

# ── Answers ───────────────────────────────────────────────────────────────────

@router.get("/questions/{question_id}/answers")
async def list_answers(question_id: str):
    try:
        res = await get_answers_controller(question_id)
        return BaseResponse(success=True, data=res, message="OK")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.post("/questions/{question_id}/answers")
async def create_answer(
    question_id: str,
    body: str = Form(...),
    image: Optional[UploadFile] = File(None),
    user=Depends(get_current_user)
):
    try:
        image_url = None
        if image and image.filename:
            content = await image.read()
            if not content:
                return BaseResponse(success=False, data=None, message="Image file is empty")

            ext = image.filename.rsplit(".", 1)[-1].lower()
            path = f"qa-images/{uuid.uuid4()}.{ext}"
            content_type = image.content_type or f"image/{ext}"

            supabase.storage.from_("files").upload(
                path, content, {"content-type": content_type}
            )
            image_url = supabase.storage.from_("files").get_public_url(path)

        res = await create_answer_controller(user, question_id, body, image_url)
        return BaseResponse(success=True, data={"id": res}, message="Answer posted")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.post("/answers/{answer_id}/like")
async def like_answer(answer_id: str, user=Depends(get_current_user)):
    try:
        res = await like_answer_controller(user, answer_id)
        return BaseResponse(success=True, data=res, message="OK")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))
