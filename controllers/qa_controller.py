from services.qa_service import (
    create_question_service, get_all_questions_service,
    get_question_by_id_service, create_answer_service,
    get_answers_for_question_service, toggle_answer_like_service,
    get_user_questions_service, delete_question_service
)

async def create_question_controller(user, body, tags):
    doc = {
        "user_id": user["user_id"],
        "body": body,
        "tags": tags,
        "created_at": __import__('datetime').datetime.utcnow()
    }
    return await create_question_service(doc)

async def get_all_questions_controller():
    return await get_all_questions_service()

async def get_question_controller(question_id):
    return await get_question_by_id_service(question_id)

async def create_answer_controller(user, question_id, body, image_url=None):
    doc = {
        "question_id": question_id,
        "user_id": user["user_id"],
        "body": body,
        "image_url": image_url,
        "likes": [],
        "created_at": __import__('datetime').datetime.utcnow()
    }
    return await create_answer_service(doc)

async def get_answers_controller(question_id):
    return await get_answers_for_question_service(question_id)

async def like_answer_controller(user, answer_id):
    return await toggle_answer_like_service(answer_id, user["user_id"])

async def get_user_questions_controller(user):
    return await get_user_questions_service(user["user_id"])

async def delete_question_controller(user, question_id):
    return await delete_question_service(question_id, user["user_id"])
