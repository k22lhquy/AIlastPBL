import asyncio
from configs.database import db

async def run():
    print("Finding all user records for lehuuquy...")
    users = await db["users"].find({"name": "lehuuquy"}).to_list(None)
    for u in users:
        print("USER:", u)
        
    print("\nFinding all auth_accounts for lehuuquy...")
    auths = await db["auth_accounts"].find({"username": "lehuuquy"}).to_list(None)
    for a in auths:
        print("AUTH:", a)
        
    # Lấy auth record mới nhất và đồng bộ isAdmin cho user_id tương ứng
    if auths:
        latest_auth = auths[-1]
        from bson import ObjectId
        user_id = latest_auth["userId"]
        print(f"\nForce mapping Admin to user_id: {user_id}")
        res = await db["users"].update_many({"_id": ObjectId(user_id)}, {"$set": {"isAdmin": True}})
        print("Mapped updated returned:", res.modified_count)

if __name__ == "__main__":
    asyncio.run(run())
