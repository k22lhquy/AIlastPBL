from services.community_service import create_post_service, get_all_posts_service, toggle_like_service, report_post_service

async def create_post_controller(user_data, post_req):
    post_dict = post_req.dict()
    doc = {
        "userId": user_data["user_id"],
        "username": user_data.get("username", "Unknown"),
        "title": post_dict["title"],
        "description": post_dict["description"],
        "fileId": post_dict["file_id"],
        "fileName": post_dict["file_name"],
        "storageUrl": post_dict.get("storage_url")
    }
    
    post_id = await create_post_service(doc)
    return {"id": post_id}

async def get_all_posts_controller():
    posts = await get_all_posts_service()
    return posts

async def toggle_like_controller(user_data, post_id: str):
    return await toggle_like_service(post_id, user_data["user_id"])

async def report_post_controller(user_data, post_id: str):
    return await report_post_service(post_id, user_data["user_id"])
