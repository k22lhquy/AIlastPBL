from configs.database import db
from models.message_model import Message
from datetime import datetime
import numpy as np
import asyncio
from langchain_core.documents import Document
from libs.ai.embedding import get_embedding_model
from libs.ai.reranker import get_reranker_model
from libs.ai.bm25_retriever import build_bm25, bm25_search, reciprocal_rank_fusion
from libs.ai.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, MAX_OUTPUT_TOKENS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

message_collection = db["messages"]
file_chunks_collection = db["file_chunks"]
upload_file_collection = db["uploaded_files"]

async def search_community_posts(q_vec: list, top_k: int = 3, threshold: float = 0.45):
    """Semantic search on community file chunks using pre-computed embeddings."""
    try:
        community_chunks = await file_chunks_collection.find(
            {"isCommunity": True}
        ).to_list(None)
        if not community_chunks:
            return []
        
        q_vec_np = np.array(q_vec)
        q_norm = np.linalg.norm(q_vec_np)
        if q_norm == 0:
            return []
        
        scored = []
        for chunk in community_chunks:
            if not chunk.get("embedding"):
                continue
            c_vec_np = np.array(chunk["embedding"])
            c_norm = np.linalg.norm(c_vec_np)
            if c_norm == 0:
                continue
            score = float(np.dot(q_vec_np, c_vec_np) / (q_norm * c_norm))
            if score >= threshold:
                scored.append((score, chunk.get("fileId", "")))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Deduplicate by fileId
        seen_file_ids = []
        for score, fid in scored:
            if fid not in seen_file_ids:
                seen_file_ids.append(fid)
            if len(seen_file_ids) >= top_k:
                break
        
        if not seen_file_ids:
            return []
        
        # Lookup posts from file IDs
        from bson import ObjectId
        posts = await db["posts"].find({"fileId": {"$in": seen_file_ids}}).to_list(None)
        result = []
        for p in posts:
            result.append({
                "id": str(p["_id"]),
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "username": p.get("username", ""),
                "userId": p.get("userId", "")
            })
        return result[:top_k]
    except Exception as e:
        print(f"[community_posts_search] error: {e}")
        return []

async def search_community_qa(question_text: str, top_k: int = 3):
    """Keyword regex search on Q&A questions."""
    try:
        import re
        escaped = re.escape(question_text[:100])
        pattern = f".*{escaped}.*"
        # Try full phrase first, if too few results generalize to individual words
        qa_cursor = await db["questions"].find({
            "$or": [
                {"body": {"$regex": pattern, "$options": "i"}},
                {"tags": {"$elemMatch": {"$regex": pattern, "$options": "i"}}}
            ]
        }).to_list(top_k)
        
        if not qa_cursor:
            # Fallback: search individual meaningful words
            words = [w for w in re.split(r'\s+', question_text) if len(w) > 3]
            if not words:
                return []
            word_query = {"$or": [{"body": {"$regex": re.escape(w), "$options": "i"}} for w in words[:5]]}
            qa_cursor = await db["questions"].find(word_query).limit(top_k).to_list(top_k)
        
        return [{
            "id": str(q["_id"]),
            "body": q.get("body", ""),
            "username": q.get("username", ""),
            "user_id": q.get("user_id", ""),
            "answer_count": q.get("answer_count", 0)
        } for q in qa_cursor]
    except Exception as e:
        print(f"[community_qa_search] error: {e}")
        return []

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
    
    # 0. Lấy lịch sử hội thoại từ MongoDB
    cursor = message_collection.find({
        "conversationId": conversationId, 
        "_id": {"$ne": user_msg_result.inserted_id}
    }).sort("timestamp", 1) # Lấy cũ đến mới
    history_docs = await cursor.to_list(None)
    
    # Chỉ lấy 10 lượt gần nhất
    history_docs = history_docs[-10:]
    history_text = ""
    if history_docs:
        lines = []
        for doc in history_docs:
            role_name = "User" if doc.get("role") == "user" else "Bot"
            lines.append(f"{role_name}: {doc.get('content')}")
        history_text = "\n".join(lines)
    
    search_question = message
    if history_text:
        # Rephrase dựa vào lịch sử
        from langchain_core.prompts import PromptTemplate
        prompt_rephrase = PromptTemplate(
            input_variables=["history", "question"],
            template="""Dựa vào lịch sử hội thoại bên dưới, hãy viết lại câu hỏi mới nhất thành 1 câu hỏi độc lập, đầy đủ nghĩa, không cần đọc lịch sử vẫn hiểu được.
Quy tắc:
- Nếu câu hỏi đã rõ ràng, độc lập → giữ nguyên
- Nếu câu hỏi dùng "thế còn", "còn", "vậy thì", đại từ "nó", "đó" → bổ sung context
- Chỉ trả về câu hỏi đã viết lại, không giải thích thêm

Lịch sử hội thoại:
{history}

Câu hỏi mới: {question}
Câu hỏi đã viết lại:"""
        )
        llm_rephrase = ChatOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY, model=LLM_MODEL, temperature=0)
        rephrase_chain = prompt_rephrase | llm_rephrase | StrOutputParser()
        def do_rephrase():
            return rephrase_chain.invoke({"history": history_text, "question": message}).strip()
            
        search_question_raw = await asyncio.to_thread(do_rephrase)
        if search_question_raw:
            search_question = search_question_raw
            if search_question != message:
                print(f"🔄 Rephrase: '{message}' → '{search_question}'")
    
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
                
            mq_result = await asyncio.to_thread(get_multi_queries, search_question)
            extra_questions = [q.strip() for q in mq_result.strip().split("\n") if q.strip()]
            all_questions = [search_question] + extra_questions
            print(f"\n🔍 Multi-Query — các câu hỏi được dùng để search:")
            for i, q in enumerate(all_questions, 1):
                print(f"   {i}. {q}")

            # 3. Embed tất cả các câu hỏi
            def embed_multi_queries(texts):
                em = get_embedding_model()
                return [em.embed_query(t) for t in texts]
                
            q_vecs = await asyncio.to_thread(embed_multi_queries, all_questions)
            
            # [HYBRID SEARCH] Bước 3b: Xây dựng BM25 index từ chunks
            def build_bm25_index():
                return build_bm25(chunks)
            bm25_model, bm25_chunks = await asyncio.to_thread(build_bm25_index)
            
            # 4. [HYBRID SEARCH] Chạy cả Vector Search và BM25 Search, gộp bằng RRF
            all_docs = []
            for q_vec, question in zip(q_vecs, all_questions):
                # --- Vector Search (Cosine Similarity) ---
                q_vec_np = np.array(q_vec)
                q_norm = np.linalg.norm(q_vec_np)
                
                vector_scored = []
                for chunk in chunks:
                    if "embedding" not in chunk or not chunk["embedding"]:
                        continue
                    c_vec_np = np.array(chunk["embedding"])
                    c_norm = np.linalg.norm(c_vec_np)
                    if c_norm == 0 or q_norm == 0:
                        score = 0.0
                    else:
                        score = float(np.dot(q_vec_np, c_vec_np) / (q_norm * c_norm))
                    vector_scored.append((score, chunk.get("content", ""), chunk.get("fileId", "")))
                vector_scored.sort(key=lambda x: x[0], reverse=True)
                vector_top = vector_scored[:10]  # Lấy top 10 cho RRF

                # --- BM25 Search (Keyword Match) ---
                def run_bm25(q):
                    return bm25_search(bm25_model, bm25_chunks, q, top_k=10)
                bm25_top = await asyncio.to_thread(run_bm25, question)
                
                # --- Reciprocal Rank Fusion (Gộp kết quả) ---
                fused = reciprocal_rank_fusion(vector_top, bm25_top, k=60)
                
                # Lấy top 5 sau khi fuse (đủ để reranker chọn thêm)
                all_docs.extend(fused[:5])
                
            # Bỏ trùng lặp (dựa theo nội dung 120 ký tự đầu)
            seen = set()
            unique_docs = []
            for doc in all_docs:
                key = doc[1][:120]
                if key not in seen:
                    seen.add(key)
                    unique_docs.append(doc)
            
            print(f"   → [Hybrid] {len(all_docs)} chunks total, {len(unique_docs)} sau khi bỏ trùng (RRF fused)\n")
            
            # 5. Reranking
            if unique_docs:
                docs_to_rerank = [Document(page_content=c[1], metadata={"score": c[0], "fileId": c[2]}) for c in unique_docs]
                reranker = get_reranker_model()
                
                # Rerank against the rephrased search_question
                ranked_docs = await asyncio.to_thread(reranker.rerank, search_question, docs_to_rerank)
                
                context_text = "\n\n---\n\n".join([f"[Đoạn ngữ cảnh] {c.page_content}" for c in ranked_docs])
                
                file_map = {str(f["_id"]): f.get("fileName", "Unknown File") for f in files}
                final_sources = []
                for d in ranked_docs:
                    fid = str(d.metadata.get("fileId", ""))
                    final_sources.append({
                        "file_id": fid,
                        "file_name": file_map.get(fid, "Unknown File"),
                        "content": d.page_content
                    })
            else:
                context_text = ""
                final_sources = []
            
    # 3. Tạo prompt và gọi LLM
    prompt = ChatPromptTemplate.from_template("""
Bạn là trợ lý thông minh. Hãy trả lời câu hỏi CHỈ DỰA TRÊN thông tin trong lịch sử hội thoại và tài liệu dưới đây.
Nếu thông tin không có trong tài liệu và lịch sử, hãy nói: "Tài liệu không đề cập đến vấn đề này."
Bạn có thể trả lời bình thường nếu câu hỏi thiên về giao tiếp thông thường.

=== LỊCH SỬ HỘI THOẠI GẦN ĐÂY ===
{history}

=== NỘI DUNG TÀI LIỆU ===
{context}

=== CÂU HỎI MỚI ===
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
    
    def generate_answer(ctx, hist, q):
        hist_input = hist if hist else "(Chưa có lịch sử)"
        return chain.invoke({"context": ctx, "history": hist_input, "question": q})
        
    try:
        answer = await asyncio.to_thread(generate_answer, context_text, history_text, message)
    except Exception as e:
        answer = "Xin lỗi, đã có lỗi kết nối đến AI. Vui lòng thử lại sau. Chi tiết lỗi: " + str(e)
    
    # --- Community-aware search (chạy song song với LLM, không chặn pipeline) ---
    community_references = {"posts": [], "questions": []}
    try:
        # Dùng q_vec từ embedding bước trước nếu có, nếu không thì embed nhanh
        if 'q_vecs' in locals() and q_vecs:
            q_vec_for_community = q_vecs[0]  # Dùng vector của câu hỏi gốc
        else:
            def embed_one(text):
                return get_embedding_model().embed_query(text)
            q_vec_for_community = await asyncio.to_thread(embed_one, search_question)
        
        comm_posts, comm_qa = await asyncio.gather(
            search_community_posts(q_vec_for_community),
            search_community_qa(search_question)
        )
        community_references = {"posts": comm_posts, "questions": comm_qa}
    except Exception as e:
        print(f"[community_search] error: {e}")
    
    # 4. Lưu tin nhắn bot
    bot_mess = Message(
        conversationId=conversationId,
        role="bot",
        content=answer,
        timestamp=datetime.utcnow(),
        sources=final_sources if 'final_sources' in locals() else [],
        community_references=community_references if community_references.get("posts") or community_references.get("questions") else None
    ).dict(exclude_none=True)
    bot_result = await message_collection.insert_one(bot_mess)

    # [ADMIN] Track token usage without blocking
    from bson import ObjectId
    tokens_used = len(answer) // 4 + len(context_text) // 4
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$inc": {"tokensUsed": tokens_used}}
    )



    return {
        "message": message,
        "answer": answer,
        "sources": bot_mess.get("sources", []),
        "community_references": bot_mess.get("community_references", None),
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