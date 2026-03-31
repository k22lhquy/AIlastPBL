from libs.hash import verify_password

# giả lập DB
fake_auth_db = [
    {
        "userId": "1",
        "username": "admin",
        "password": "$2b$12$KIXQy..."  # password đã hash
    }
]

def login(username: str, password: str):
    # 1. tìm user
    user = next((u for u in fake_auth_db if u["username"] == username), None)

    if not user:
        raise Exception("User not found")

    # 2. verify password
    if not verify_password(password, user["password"]):
        raise Exception("Wrong password")

    # 3. trả kết quả (sau này thay bằng JWT)
    return {
        "message": "Login success",
        "userId": user["userId"]
    }