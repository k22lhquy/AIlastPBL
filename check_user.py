import asyncio
from configs.database import db

async def run():
    user = await db["users"].find_one({"email": "lehuuquy@gmail.com"})
    print("User from DB:", user)

if __name__ == "__main__":
    asyncio.run(run())
