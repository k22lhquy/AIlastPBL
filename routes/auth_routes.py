from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from controllers import auth_controller
from libs.baseResponse import BaseResponse
from middlewares.auth_middleware import get_current_user

router = APIRouter()


class AuthRequest(BaseModel):
    username: str
    password: str
    confirm_password: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


@router.post("/register")
async def register(data: AuthRequest):
    try:
        if data.confirm_password and data.password != data.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
            
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


@router.post("/refresh")
async def refresh_token(data: RefreshTokenRequest):
    try:
        from libs.jwt import verify_token, create_access_token, create_refresh_token
        payload = verify_token(data.refresh_token)
        
        if payload.get("type") != "refresh":
            return BaseResponse(success=False, data=None, message="Invalid token type")
            
        user_id = payload.get("user_id")
        username = payload.get("username")
        
        new_access = create_access_token({"user_id": user_id, "username": username})
        new_refresh = create_refresh_token({"user_id": user_id, "username": username})
        
        return BaseResponse(success=True, data={
            "access_token": new_access,
            "refresh_token": new_refresh
        }, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))
    
@router.post("/change-password")
async def change_password(data: ChangePasswordRequest, user=Depends(get_current_user)):
    try:
        if data.new_password != data.confirm_password:
            raise HTTPException(status_code=400, detail="Mật khẩu xác nhận không khớp")
        
        from services import auth_service
        result = await auth_service.change_password(user["user_id"], data.old_password, data.new_password)
        return BaseResponse(success=True, data=result, message="Success")
    except Exception as e:
        msg = e.detail if hasattr(e, "detail") else str(e)
        return BaseResponse(success=False, data=None, message=msg)

@router.get("/test")
def test():
    try:
        return BaseResponse(success=True, data={"message": "Auth route is working!"}, message="Success")
    except Exception as e:
        msg = e.detail if isinstance(e, HTTPException) else str(e)
        return BaseResponse(success=False, data=None, message=msg)