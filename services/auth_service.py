from configs.database import db
from libs.hash import hash_password, verify_password
from libs.jwt import create_access_token

auth_collection = db["auth_accounts"]
# user_collection = db["users"]


# REGISTER
async def register(username: str, password: str):
    existing = await auth_collection.find_one({"username": username})

    if existing:
        raise Exception("Username already exists")

    hashed = hash_password(password)
    
    # user = await user_collection.insert_one({
    #     "username": username,
    #     "created_at": db.client.server_info()["localTime"]
    # })

    result = await auth_collection.insert_one({
        "username": username,
        "password": hashed
    })

    return {
        "message": "Register success",
        "userId": str(result.inserted_id)
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