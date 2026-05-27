from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from middlewares.auth_middleware import get_current_user
from configs.database import db
from bson import ObjectId
from libs.baseResponse import BaseResponse
from services.community_service import get_user_posts_service
from services.qa_service import get_user_questions_service

router = APIRouter()

class ThemeUpdateRequest(BaseModel):
    isDark: bool

@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    try:
        user_record = await db["users"].find_one({"_id": ObjectId(user["user_id"])})
        theme_is_dark = user_record.get("themeIsDark", False) if user_record else False
        is_admin = user_record.get("isAdmin", False) if user_record else False
        
        user["themeIsDark"] = theme_is_dark
        user["isAdmin"] = is_admin
        
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

@router.get("/search/query")
async def search_users(q: str, user=Depends(get_current_user)):
    try:
        import re
        escaped_q = re.escape(q)
        regex_pattern = f".*{escaped_q}.*"
        query = {
            "$or": [
                {"username": {"$regex": regex_pattern, "$options": "i"}},
                {"email": {"$regex": regex_pattern, "$options": "i"}}
            ]
        }
        pipeline = [
            {"$match": query},
            {"$set": {"likeCount": {"$size": {"$ifNull": ["$likes", []]}}}},
            {"$sort": {"likeCount": -1}},
            {"$limit": 50}
        ]
        users = await db["users"].aggregate(pipeline).to_list(100)
        
        result = [
            {
                "id": str(u["_id"]),
                "username": u.get("username", "Unknown"),
                "email": u.get("email", ""),
                "likes": u.get("likes", [])
            } for u in users
        ]
        return BaseResponse(success=True, data=result, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/{target_id}")
async def get_user_public_profile(target_id: str, user=Depends(get_current_user)):
    try:
        user_record = await db["users"].find_one({"_id": ObjectId(target_id)})
        if not user_record:
            return BaseResponse(success=False, data=None, message="User not found")
        
        return BaseResponse(success=True, data={
            "id": str(user_record["_id"]),
            "username": user_record.get("username", ""),
            "email": user_record.get("email", ""),
            "likes": user_record.get("likes", [])
        }, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.patch("/{target_id}/like")
async def toggle_like_user(target_id: str, user=Depends(get_current_user)):
    try:
        from bson import ObjectId
        user_id = user["user_id"]
        target = await db["users"].find_one({"_id": ObjectId(target_id)})
        if not target:
            return BaseResponse(success=False, data=None, message="User not found")
            
        likes = target.get("likes", [])
        if user_id in likes:
            likes.remove(user_id)
        else:
            likes.append(user_id)
            
        await db["users"].update_one(
            {"_id": ObjectId(target_id)},
            {"$set": {"likes": likes}}
        )
        return BaseResponse(success=True, data={"likes": likes}, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/{target_id}/posts")
async def get_target_user_posts(target_id: str, user=Depends(get_current_user)):
    try:
        res = await get_user_posts_service(target_id)
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))

@router.get("/{target_id}/questions")
async def get_target_user_questions(target_id: str, user=Depends(get_current_user)):
    try:
        res = await get_user_questions_service(target_id)
        return BaseResponse(success=True, data=res, message="Success")
    except Exception as e:
        return BaseResponse(success=False, data=None, message=str(e))