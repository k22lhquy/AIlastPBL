from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from controllers import auth_controller
from libs.baseResponse import BaseResponse

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(data: AuthRequest):
    try:
        result = await auth_controller.register(data)
        return BaseResponse(success=True, data=result, message="Success")
    except HTTPException as e:
        return BaseResponse(success=False, data=None, message=str(e.detail))
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))


@router.post("/login")
async def login(data: AuthRequest):
    try:
        result = await auth_controller.login(data)
        return BaseResponse(success=True, data=result, message="Success")
    except Exception as e:
        msg = e.detail if isinstance(e, HTTPException) else str(e)
        return BaseResponse(success=False, data=None, message=msg)
    
@router.get("/test")
def test():
    try:
        return BaseResponse(success=True, data={"message": "Auth route is working!"}, message="Success")
    except Exception as e:
        msg = e.detail if isinstance(e, HTTPException) else str(e)
        return BaseResponse(success=False, data=None, message=msg)