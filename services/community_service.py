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

async def report_post_service(post_id: str, user_id: str, reason: str):
    post_col = db["posts"]
    post = await post_col.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise Exception("Post not found")
        
    reports = post.get("reports", [])
    
    # check backward compat or duplicate user
    for r in reports:
        if isinstance(r, dict) and r.get("userId") == user_id:
            return
        elif isinstance(r, str) and r == user_id:
            return

    reports.append({"userId": user_id, "reason": reason})
    await post_col.update_one({"_id": ObjectId(post_id)}, {"$set": {"reports": reports}})
        
async def get_user_posts_service(user_id: str):
    post_col = db["posts"]
    posts = await post_col.find({"userId": user_id}).sort("createdAt", -1).to_list(None)
    
    for p in posts:
         p["id"] = str(p.pop("_id", ""))
         if "file_id" in p:
             p["fileId"] = p.pop("file_id", "")
         if "file_name" in p:
             p["fileName"] = p.pop("file_name", "")
         if "storage_url" in p:
             p["storageUrl"] = p.pop("storage_url", "")
    return posts

async def delete_post_service(post_id: str, user_id: str):
    post_col = db["posts"]
    result = await post_col.delete_one({"_id": ObjectId(post_id), "userId": user_id})
    if result.deleted_count == 0:
        raise Exception("Post not found or unauthorized")
    return {"message": "Post deleted"}
