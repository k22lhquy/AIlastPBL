import datetime

from configs.database import db
from libs.hash import hash_password, verify_password
from libs.jwt import create_access_token

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
    
    token = create_access_token({
        "user_id": user_id
    })

    return {
        "message": "Register success",
        "userId": user_id,
        "access_token": token
    }


# LOGIN
async def login(username: str, password: str):
    user = await auth_collection.find_one({"username": username})

    if not user:
        raise Exception("User not found")

    if not verify_password(password, user["password"]):
        raise Exception("Wrong password")

    token = create_access_token({
        "user_id": str(user["_id"]),
        "username": user["username"]
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }