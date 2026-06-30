from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from libs.jwt import verify_token
from configs.database import db
from bson import ObjectId

security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = verify_token(token)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_active_user(user=Depends(get_current_user)):
    user_id = user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid user session")
    
    db_user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if db_user and db_user.get("isBlocked", False):
        raise HTTPException(
            status_code=403,
            detail="Tài khoản của bạn đã bị khóa tính năng tương tác cộng đồng."
        )
    return user