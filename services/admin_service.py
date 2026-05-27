import datetime
from bson import ObjectId
from configs.database import db

# Collections
users_col = db["users"]
posts_col = db["posts"]
questions_col = db["questions"]
answers_col = db["answers"]

async def get_admin_stats_service():
    total_users = await users_col.count_documents({})
    total_posts = await posts_col.count_documents({})
    total_questions = await questions_col.count_documents({})
    
    return {
        "totalUsers": total_users,
        "totalPosts": total_posts,
        "totalQuestions": total_questions
    }

async def get_all_users_service():
    users = await users_col.find({}).sort("created_at", -1).to_list(None)
    for u in users:
        u["id"] = str(u["_id"])
        del u["_id"]
        # Đếm thống kê cho user này
        u["postsCount"] = await posts_col.count_documents({"userId": u["id"]})
        u["questionsCount"] = await questions_col.count_documents({"user_id": u["id"]})
        u["tokensUsed"] = u.get("tokensUsed", 0)
    return users

async def get_reported_content_service():
    # Posts with >= 1 reports
    reported_posts = await posts_col.find({"reports": {"$exists": True, "$not": {"$size": 0}}}).to_list(None)
    # Questions with >= 1 reports
    reported_questions = await questions_col.find({"reports": {"$exists": True, "$not": {"$size": 0}}}).to_list(None)
    
    reports_view = []
    
    for p in reported_posts:
        raw_reports = p.get("reports", [])
        reasons = [r.get("reason", "No reason provided") for r in raw_reports if isinstance(r, dict)]
        if not reasons and raw_reports:
            reasons = ["Legacy Report"] * len(raw_reports)
            
        reports_view.append({
            "id": str(p["_id"]),
            "type": "POST",
            "content": p.get("title", "") + " - " + p.get("description", ""),
            "author": p.get("username", p.get("authorName", "Unknown")),
            "reportCount": len(raw_reports),
            "reasons": reasons,
            "createdAt": p.get("createdAt")
        })
        
    for q in reported_questions:
        raw_reports = q.get("reports", [])
        reasons = [r.get("reason", "No reason provided") for r in raw_reports if isinstance(r, dict)]
        if not reasons and raw_reports:
            reasons = ["Legacy Report"] * len(raw_reports)
            
        reports_view.append({
            "id": str(q["_id"]),
            "type": "QA",
            "content": q.get("body", ""),
            "author": q.get("username", "Unknown"), # might not have "username", but we handle it on frontend
            "reportCount": len(raw_reports),
            "reasons": reasons,
            "createdAt": q.get("created_at")
        })
        
    reports_view.sort(key=lambda x: x["reportCount"], reverse=True)
    return reports_view
