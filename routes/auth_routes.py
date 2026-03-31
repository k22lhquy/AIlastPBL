from fastapi import APIRouter, HTTPException
from controllers import auth_controller
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Auth"])


# Request body
class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest):
    try:
        return auth_controller.login(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.get("/test")
def test():
    return {"message": "Auth route is working!"}