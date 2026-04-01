from fastapi import APIRouter, Depends
from middlewares.auth_middleware import get_current_user

router = APIRouter()


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    return {
        "message": "Protected route",
        "user": user
    }