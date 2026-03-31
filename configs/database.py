from motor.motor_asyncio import AsyncIOMotorClient
from configs.config import MONGO_URI, DB_NAME

client = AsyncIOMotorClient(MONGO_URI)

db = client[DB_NAME]

print("🚀 MongoDB connected")