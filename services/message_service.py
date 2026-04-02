from configs.database import db
from models.message_model import Message
from datetime import datetime
import numpy as np
import asyncio
from libs.ai.embedding import get_embedding_model
from libs.ai.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, MAX_OUTPUT_TOKENS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

message_collection = db["messages"]
file_chunks_collection = db["file_chunks"]
upload_file_collection = db["uploaded_files"]

async def message_service(user_id: str, message: str, conversationId: str):
    if not message:
        raise ValueError("Message content is required")
    if message.strip() == "":
        raise ValueError("Message content cannot be empty")
    
    mess = Message(
        conversationId=conversationId,
        role="user",
        content=message,
        timestamp=datetime.utcnow()
    ).dict(exclude_none=True)
    
    user_msg_result = await message_collection.insert_one(mess)
    
    # 1. Tìm tất cả files của cuộc trò chuyện này
    files = await upload_file_collection.find({"conversationId": conversationId}).to_list(None)
    file_ids = [str(f["_id"]) for f in files]
    
    context_text = ""
    if file_ids:
        chunks = await file_chunks_collection.find({"fileId": {"$in": file_ids}}).to_list(None)
        if chunks:
            # 2. Sinh thêm câu hỏi (Multi-Query)
            from langchain_core.prompts import PromptTemplate
            prompt_mq = PromptTemplate(
                input_variables=["question"],
                template="""Tạo ra 3 câu hỏi khác nhau cùng ý nghĩa với câu hỏi gốc bên dưới. Mục đích là tìm kiếm tài liệu từ nhiều góc độ khác nhau. Yêu cầu: Viết bằng tiếng Việt, mỗi câu hỏi trên 1 dòng, không đánh số, không giải thích. Trả về đúng 3 dòng.
Câu hỏi gốc: {question}"""
            )
            llm_mq = ChatOpenAI(
                base_url=LLM_BASE_URL,
                api_key=LLM_API_KEY,
                model=LLM_MODEL,
                temperature=0
            )
            mq_chain = prompt_mq | llm_mq | StrOutputParser()
            def get_multi_queries(q):
                return mq_chain.invoke({"question": q})
                
            mq_result = await asyncio.to_thread(get_multi_queries, message)
            extra_questions = [q.strip() for q in mq_result.strip().split("\n") if q.strip()]
            all_questions = [message] + extra_questions
            print(f"\n🔍 Multi-Query — các câu hỏi được dùng để search:")
            for i, q in enumerate(all_questions, 1):
                print(f"   {i}. {q}")

            # 3. Embed tất cả các câu hỏi
            def embed_multi_queries(texts):
                em = get_embedding_model()
                return [em.embed_query(t) for t in texts]
                
            q_vecs = await asyncio.to_thread(embed_multi_queries, all_questions)
            
            # 4. Search song song & gộp kết quả
            all_docs = []
            for q_vec in q_vecs:
                q_vec_np = np.array(q_vec)
                q_norm = np.linalg.norm(q_vec_np)
                
                scored_chunks = []
                for chunk in chunks:
                    if "embedding" not in chunk or not chunk["embedding"]:
                        continue
                    c_vec_np = np.array(chunk["embedding"])
                    c_norm = np.linalg.norm(c_vec_np)
                    if c_norm == 0 or q_norm == 0:
                        score = 0
                    else:
                        score = np.dot(q_vec_np, c_vec_np) / (q_norm * c_norm)
                    scored_chunks.append((score, chunk["content"]))
                
                # Lấy Top 3 chunks cho mỗi câu hỏi
                scored_chunks.sort(key=lambda x: x[0], reverse=True)
                top_k = scored_chunks[:3]
                all_docs.extend(top_k)
                
            # Bỏ trùng lặp (dựa theo nội dung 100 ký tự đầu để nhận biết)
            seen = set()
            unique_docs = []
            for doc in all_docs:
                key = doc[1][:100]
                if key not in seen:
                    seen.add(key)
                    unique_docs.append(doc)
            
            print(f"   → Tìm được {len(all_docs)} chunks, còn {len(unique_docs)} sau khi bỏ trùng\n")
            context_text = "\n\n---\n\n".join([f"[Đoạn ngữ cảnh] {c[1]}" for c in unique_docs])
            
    # 3. Tạo prompt và gọi LLM
    prompt = ChatPromptTemplate.from_template("""
Bạn là trợ lý thông minh. Hãy trả lời câu hỏi CHỈ DỰA TRÊN thông tin trong tài liệu dưới đây.
Nếu thông tin không có trong tài liệu, hãy nói: "Tài liệu không đề cập đến vấn đề này."
Bạn có thể trả lời bình thường nếu câu hỏi thiên về giao tiếp thông thường.

=== NỘI DUNG TÀI LIỆU ===
{context}

=== CÂU HỎI ===
{question}

=== TRẢ LỜI ===
""")
    
    llm = ChatOpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=MAX_OUTPUT_TOKENS,
    )
    chain = prompt | llm | StrOutputParser()
    
    def generate_answer(ctx, q):
        return chain.invoke({"context": ctx, "question": q})
        
    try:
        answer = await asyncio.to_thread(generate_answer, context_text, message)
    except Exception as e:
        answer = "Xin lỗi, đã có lỗi kết nối đến AI. Vui lòng thử lại sau. Chi tiết lỗi: " + str(e)
    
    # 4. Lưu tin nhắn bot
    bot_mess = Message(
        conversationId=conversationId,
        role="bot",
        content=answer,
        timestamp=datetime.utcnow()
    ).dict(exclude_none=True)
    bot_result = await message_collection.insert_one(bot_mess)

    return {
        "message": message,
        "answer": answer,
        "user_message_id": str(user_msg_result.inserted_id),
        "bot_message_id": str(bot_result.inserted_id),
        "conversationId": conversationId
    }

async def get_messages_service(user_id: str, conversationId: str):
    messages_cursor = message_collection.find({"conversationId": conversationId}).sort("timestamp", 1)
    messages = []
    async for message in messages_cursor:
        message["id"] = str(message["_id"])
        del message["_id"]
        messages.append(message)
    return messages
# chỉnh lại return có status code và message rõ ràng hơn, có thể trả về id của message mới tạo để client dễ dàng quản lý sau này.