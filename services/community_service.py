from configs.database import db
from models.post_model import PostModel
from bson import ObjectId
import datetime

async def create_post_service(post_data: dict):
    post_col = db["posts"]
    post_data["createdAt"] = datetime.datetime.utcnow()
    post_data["likes"] = []
    post_data["reports"] = []
    
    result = await post_col.insert_one(post_data)
    return str(result.inserted_id)

async def get_all_posts_service():
    post_col = db["posts"]
    posts = await post_col.find().sort("createdAt", -1).to_list(None)
    
    for p in posts:
         p["id"] = str(p.pop("_id", ""))
         if "file_id" in p:
             p["fileId"] = p.pop("file_id", "")
         if "file_name" in p:
             p["fileName"] = p.pop("file_name", "")
         if "storage_url" in p:
             p["storageUrl"] = p.pop("storage_url", "")
    return posts

async def toggle_like_service(post_id: str, user_id: str):
    post_col = db["posts"]
    post = await post_col.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise Exception("Post not found")
        
    likes = post.get("likes", [])
    if user_id in likes:
        likes.remove(user_id)
        action = "unliked"
    else:
        likes.append(user_id)
        action = "liked"
        
    await post_col.update_one({"_id": ObjectId(post_id)}, {"$set": {"likes": likes}})
    return {"action": action, "likes_count": len(likes)}

async def report_post_service(post_id: str, user_id: str):
    post_col = db["posts"]
    post = await post_col.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise Exception("Post not found")
        
    reports = post.get("reports", [])
    if user_id not in reports:
        reports.append(user_id)
        await post_col.update_one({"_id": ObjectId(post_id)}, {"$set": {"reports": reports}})
        
    return {"message": "Report submitted"}
