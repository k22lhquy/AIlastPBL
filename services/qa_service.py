from bson import ObjectId
from configs.database import db

questions_col = db["questions"]
answers_col = db["answers"]
users_col = db["users"]

def _fmt_q(q):
    q["id"] = str(q.pop("_id"))
    return q

def _fmt_a(a):
    a["id"] = str(a.pop("_id"))
    return a

async def get_username(user_id: str) -> str:
    try:
        user = await users_col.find_one({"_id": ObjectId(user_id)})
        if user:
            return user.get("username", "Unknown")
    except Exception:
        pass
    return "Unknown"

# ── Questions ─────────────────────────────────────────────────────────────────

async def create_question_service(doc: dict) -> str:
    res = await questions_col.insert_one(doc)
    return str(res.inserted_id)

async def get_all_questions_service():
    cursor = questions_col.find().sort("created_at", -1)
    questions = await cursor.to_list(length=100)
    result = []
    for q in questions:
        q = _fmt_q(q)
        q["username"] = await get_username(q.get("user_id", ""))
        # count answers
        count = await answers_col.count_documents({"question_id": q["id"]})
        q["answer_count"] = count
        result.append(q)
    return result

async def get_question_by_id_service(question_id: str):
    q = await questions_col.find_one({"_id": ObjectId(question_id)})
    if not q:
        return None
    q = _fmt_q(q)
    q["username"] = await get_username(q.get("user_id", ""))
    return q

# ── Answers ───────────────────────────────────────────────────────────────────

async def create_answer_service(doc: dict) -> str:
    res = await answers_col.insert_one(doc)
    return str(res.inserted_id)

async def get_answers_for_question_service(question_id: str):
    # sort by number of likes descending
    pipeline = [
        {"$match": {"question_id": question_id}},
        {"$addFields": {"like_count": {"$size": "$likes"}}},
        {"$sort": {"like_count": -1, "created_at": 1}}
    ]
    cursor = answers_col.aggregate(pipeline)
    answers = await cursor.to_list(length=200)
    result = []
    for a in answers:
        a = _fmt_a(a)
        a["username"] = await get_username(a.get("user_id", ""))
        result.append(a)
    return result

async def toggle_answer_like_service(answer_id: str, user_id: str):
    answer = await answers_col.find_one({"_id": ObjectId(answer_id)})
    if not answer:
        raise Exception("Answer not found")
    likes = answer.get("likes", [])
    if user_id in likes:
        likes.remove(user_id)
    else:
        likes.append(user_id)
    await answers_col.update_one({"_id": ObjectId(answer_id)}, {"$set": {"likes": likes}})
    return {"likes": len(likes)}

async def get_user_questions_service(user_id: str):
    cursor = questions_col.find({"user_id": user_id}).sort("created_at", -1)
    questions = await cursor.to_list(length=100)
    result = []
    for q in questions:
        q = _fmt_q(q)
        q["username"] = await get_username(q.get("user_id", ""))
        count = await answers_col.count_documents({"question_id": q["id"]})
        q["answer_count"] = count
        result.append(q)
    return result

async def delete_question_service(question_id: str, user_id: str):
    result = await questions_col.delete_one({"_id": ObjectId(question_id), "user_id": user_id})
    if result.deleted_count == 0:
        raise Exception("Question not found or unauthorized")
    await answers_col.delete_many({"question_id": question_id})
    return {"message": "Question deleted"}
