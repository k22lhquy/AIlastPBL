from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from middlewares.auth_middleware import get_current_user
from configs.database import db
from bson import ObjectId
from libs.baseResponse import BaseResponse

router = APIRouter()

class ThemeUpdateRequest(BaseModel):
    isDark: bool

@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    try:
        user_record = await db["users"].find_one({"_id": ObjectId(user["user_id"])})
        theme_is_dark = user_record.get("themeIsDark", False) if user_record else False
        
        user["themeIsDark"] = theme_is_dark
        
        return BaseResponse(success=True, data={
            "user": user
        }, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.patch("/me/theme")
async def update_theme(data: ThemeUpdateRequest, user=Depends(get_current_user)):
    try:
        await db["users"].update_one(
            {"_id": ObjectId(user["user_id"])},
            {"$set": {"themeIsDark": data.isDark}}
        )
        return BaseResponse(success=True, data=None, message="Theme updated")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))