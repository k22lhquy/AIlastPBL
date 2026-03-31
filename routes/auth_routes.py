from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from controllers import auth_controller

router = APIRouter(prefix="/auth", tags=["Auth"])


class AuthRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(data: AuthRequest):
    try:
        return await auth_controller.register(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
async def login(data: AuthRequest):
    try:
        return await auth_controller.login(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/test")
def test():
    return {"message": "Auth route is working!"}