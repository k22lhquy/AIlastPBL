import asyncio
from configs.database import db

async def run():
    res = await db["users"].update_many({"email": "lehuuquy@gmail.com"}, {"$set": {"isAdmin": True}})
    print("Updated admin count:", res.modified_count)

if __name__ == "__main__":
    asyncio.run(run())
