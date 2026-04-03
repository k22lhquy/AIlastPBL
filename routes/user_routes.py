from fastapi import APIRouter, Depends, HTTPException
from middlewares.auth_middleware import get_current_user
from libs.baseResponse import BaseResponse

router = APIRouter()


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    try:
        return BaseResponse(success=True, data={
            "message": "Protected route",
            "user": user
        }, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))