from fastapi import Depends, HTTPException
from middlewares.auth_middleware import get_current_user
from configs.database import db
from bson import ObjectId

async def require_admin(user=Depends(get_current_user)):
    user_record = await db["users"].find_one({"_id": ObjectId(user["user_id"])})
    if not user_record:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user_record.get("isAdmin", False):
        raise HTTPException(status_code=403, detail="Forbidden: You are not an Admin")
    
    # Return user record along with token payload details
    user["isAdmin"] = True
    return user
