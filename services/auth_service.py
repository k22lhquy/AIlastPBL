import datetime

from configs.database import db
from libs.hash import hash_password, verify_password
from libs.jwt import create_access_token, create_refresh_token

auth_collection = db["auth_accounts"]
user_collection = db["users"]


# REGISTER
async def register(username: str, password: str):
    existing = await auth_collection.find_one({"username": username})

    if existing:
        raise Exception("Username already exists")

    hashed = hash_password(password)
    
    user = await user_collection.insert_one({
        "email": f"{username}@gmail.com",
        "name": username,
        "created_at": datetime.datetime.utcnow()
    })
    
    user_id = str(user.inserted_id)

    await auth_collection.insert_one({
        "userId": user_id,
        "username": username,
        "password": hashed
    })
    
    access_token = create_access_token({"user_id": user_id})
    refresh_token = create_refresh_token({"user_id": user_id})

    return {
        "message": "Register success",
        "userId": user_id,
        "access_token": access_token,
        "refresh_token": refresh_token
    }


# LOGIN
async def login(username: str, password: str):
    user = await auth_collection.find_one({"username": username})

    if not user:
        raise Exception("User not found")

    if not verify_password(password, user["password"]):
        raise Exception("Wrong password")

    user_id = str(user["userId"])
    access_token = create_access_token({
        "user_id": user_id,
        "username": user["username"]
    })
    refresh_token = create_refresh_token({
        "user_id": user_id
    })

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

async def change_password(user_id: str, old_password: str, new_password: str):
    auth_acc = await auth_collection.find_one({"userId": user_id})
    if not auth_acc:
        raise Exception("Không tìm thấy thông tin xác thực người dùng")
        
    if not verify_password(old_password, auth_acc["password"]):
        raise Exception("Mật khẩu cũ không chính xác")
        
    if len(new_password) < 6:
        raise Exception("Mật khẩu mới phải từ 6 ký tự trở lên")
        
    new_hashed = hash_password(new_password)
    await auth_collection.update_one(
        {"userId": user_id},
        {"$set": {"password": new_hashed}}
    )
    return {"message": "Đổi mật khẩu thành công"}