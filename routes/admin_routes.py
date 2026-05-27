from fastapi import APIRouter, Depends
from middlewares.admin_middleware import require_admin
import controllers.admin_controller as controller
from libs.baseResponse import BaseResponse

router = APIRouter()

@router.get("/stats")
async def get_stats(user=Depends(require_admin)):
    try:
        res = await controller.get_admin_stats_controller()
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/users")
async def get_all_users(user=Depends(require_admin)):
    try:
        res = await controller.get_all_users_controller()
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

from services.community_service import get_user_posts_service
from services.qa_service import get_user_questions_service

@router.get("/users/{user_id}/posts")
async def get_user_posts(user_id: str, user=Depends(require_admin)):
    try:
        res = await get_user_posts_service(user_id)
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/users/{user_id}/questions")
async def get_user_questions(user_id: str, user=Depends(require_admin)):
    try:
        res = await get_user_questions_service(user_id)
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

from services.admin_service import get_reported_content_service

@router.get("/reports")
async def get_reports(user=Depends(require_admin)):
    try:
        res = await get_reported_content_service()
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

