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

async def search_community_posts(q_vec: list, query_text: str, top_k: int = 5, threshold: float = 0.81):
    """Semantic search on community posts (via file chunks and post metadata) with keyword fallback."""
    try:
        import numpy as np
        from bson import ObjectId
        q_vec_np = np.array(q_vec)
        q_norm = np.linalg.norm(q_vec_np)
        if q_norm == 0:
            return []
            
        # Logic Hybrid: Lấy bài nếu (Score >= 0.81) HOẶC (Keyword Match AND Score >= 0.65)
        keywords = [w.lower() for w in query_text.split() if len(w) >= 2]
        
        # 1. Search file chunks
        community_chunks = await file_chunks_collection.find({"isCommunity": True}).to_list(None)
        
        file_scored = []
        for chunk in community_chunks:
            if not chunk.get("embedding"): continue
            c_vec_np = np.array(chunk["embedding"])
            c_norm = np.linalg.norm(c_vec_np)
            if c_norm > 0:
                score = float(np.dot(q_vec_np, c_vec_np) / (q_norm * c_norm))
                
                content = chunk.get("content", "").lower()
                has_key = any(k in content for k in keywords) if keywords else False
                
                if score >= threshold or (has_key and score >= 0.65):
                    file_scored.append((score, chunk.get("fileId", "")))
        
        file_scored.sort(key=lambda x: x[0], reverse=True)
        seen_file_ids = []
        for score, fid in file_scored:
            if fid and fid not in seen_file_ids:
                seen_file_ids.append(fid)
            if len(seen_file_ids) >= top_k:
                break
                
        results_from_chunks = []
        if seen_file_ids:
            results_from_chunks = await db["posts"].find({"fileId": {"$in": seen_file_ids}}).to_list(None)
            
        # 2. Search post embeddings directly
        posts = await db["posts"].find().to_list(None)
        post_scored = []
        for p in posts:
            if not p.get("embedding"): continue
            c_vec_np = np.array(p["embedding"])
            c_norm = np.linalg.norm(c_vec_np)
            if c_norm > 0:
                score = float(np.dot(q_vec_np, c_vec_np) / (q_norm * c_norm))
                
                title = p.get("title", "").lower()
                desc = p.get("description", "").lower()
                tags = " ".join(p.get("tags", [])).lower()
                has_key = any(k in title or k in desc or k in tags for k in keywords) if keywords else False
                
                if score >= threshold or (has_key and score >= 0.65):
                     post_scored.append((score, p))
                    
        post_scored.sort(key=lambda x: x[0], reverse=True)
        results_from_posts = [s[1] for s in post_scored] # No hard slice, use threshold filter
        
        # 3. Combine
        combined = {str(p["_id"]): p for p in results_from_chunks + results_from_posts}
        
        # Trả về các post relevance nhất (chỉ lấy top_k)
        # Để sort chính xác ở đây hơi khó vì gộp 2 list, nhưng mình chỉ giới hạn size
        result = []
        for pid, p in combined.items():
            result.append({
                "id": pid,
                "title": p.get("title", ""),
                "description": p.get("description", ""),
                "username": p.get("username", ""),
                "userId": p.get("userId", ""),
                "tags": p.get("tags", [])
            })
        return result[:top_k]
    except Exception as e:
        print(f"[community_posts_search] error: {e}")
        return []

async def search_community_qa(q_vec: list, query_text: str, top_k: int = 5, threshold: float = 0.81):
    """Semantic vector search on Q&A questions with keyword fallback."""
    try:
        from bson import ObjectId
        import numpy as np
        
        q_vec_np = np.array(q_vec)
        q_norm = np.linalg.norm(q_vec_np)
        if q_norm == 0:
            return []
            
        questions = await db["questions"].find().to_list(None)
        
        keywords = [w.lower() for w in query_text.split() if len(w) >= 2]
        
        scored = []
        for q in questions:
            if not q.get("embedding"):
                continue
            c_vec_np = np.array(q["embedding"])
            c_norm = np.linalg.norm(c_vec_np)
            if c_norm > 0:
                score = float(np.dot(q_vec_np, c_vec_np) / (q_norm * c_norm))
                
                body = q.get("body", "").lower()
                tags = " ".join(q.get("tags", [])).lower()
                has_key = any(k in body or k in tags for k in keywords) if keywords else False
                
                if score >= threshold or (has_key and score >= 0.65):
                    scored.append((score, q))
                
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [{
            "id": str(s[1]["_id"]),
            "body": s[1].get("body", ""),
            "username": s[1].get("username", ""),
            "user_id": s[1].get("user_id", ""),
            "answer_count": s[1].get("answer_count", 0),
            "tags": s[1].get("tags", [])
        } for s in scored[:top_k]]
    except Exception as e:
        print(f"[community_qa_search] error: {e}")
        return []

async def message_service(user_id: str, message: str, conversationId: str, activeFileId: str = None):
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
    
    # Nếu user chọn 1 file cụ thể, chỉ query file đó
    if activeFileId and activeFileId in file_ids:
        file_ids = [activeFileId]
        print(f"🎯 Active file filter: only querying file {activeFileId}")
    
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
                
    # 5. Intent Detection / Routing (Khoanh vùng tìm kiếm)
    def detect_intent(q):
        intent_prompt = ChatPromptTemplate.from_template("""
        Câu hỏi của người dùng: "{question}"
        Hãy đánh giá xem người dùng có đang CHỈ muốn hỏi về nội dung bên trong một file, tài liệu, đoạn chat hay báo cáo cụ thể đang được đính kèm ở hiện tại, và KHÔNG muốn liên hệ các kiến thức bên ngoài hay tìm kiếm trên mạng/cộng đồng không?
        Dấu hiệu: "file này", "tài liệu này", "đoạn chat", "báo cáo tôi gửi", "trong đây", "học sinh này"...
        Nếu đúng là câu hỏi CÓ ràng buộc rõ ràng chỉ hỏi trong file/tài liệu đính kèm, hãy xuất ra chính xác chữ: TRUE
        Nếu câu hỏi hỏi chung chung, hoặc hỏi kiến thức mở, không bị ràng buộc cụ thể vào tài liệu, hãy xuất ra chính xác chữ: FALSE
        Chỉ in ra đúng 1 từ tiếng Anh in hoa (TRUE hoặc FALSE), không giải thích.
        """)
        intent_chain = intent_prompt | ChatOpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY, model=LLM_MODEL, temperature=0, max_tokens=10) | StrOutputParser()
        return intent_chain.invoke({"question": q}).strip().upper()

    try:
        is_strict_context_str = await asyncio.to_thread(detect_intent, message)
        is_strict_context = "TRUE" in is_strict_context_str
        print(f"🕵️ Intent Classification (Strict Context Only?): {is_strict_context_str} -> {is_strict_context}")
    except Exception as e:
        print(f"[intent_detection] error: {e}")
        is_strict_context = False

    # --- Community-aware search (chạy song song với LLM, không chặn pipeline) ---
    community_references = {"posts": [], "questions": []}
    if not is_strict_context:
        try:
            # Dùng q_vec từ embedding bước trước nếu có, nếu không thì embed nhanh
            if 'q_vecs' in locals() and q_vecs:
                q_vec_for_community = q_vecs[0]  # Dùng vector của câu hỏi gốc
            else:
                def embed_one(text):
                    return get_embedding_model().embed_query(text)
                q_vec_for_community = await asyncio.to_thread(embed_one, search_question)
            
            comm_posts, comm_qa = await asyncio.gather(
                search_community_posts(q_vec_for_community, query_text=search_question),
                search_community_qa(q_vec_for_community, query_text=search_question)
            )
            community_references = {"posts": comm_posts, "questions": comm_qa}
            
            # Đưa nội dung cộng đồng vào context cho LLM đọc
            if comm_posts or comm_qa:
                context_text += "\n\n=== TÀI LIỆU TỪ CỘNG ĐỒNG (Tham khảo để trả lời nếu cần thiết) ===\n"
                if comm_posts:
                    context_text += "Các bài Chia Sẻ:\n"
                    for p in comm_posts:
                        context_text += f"- Tiêu đề: {p['title']}\n  Nội dung: {p['description']}\n  Tags: {', '.join(p.get('tags', []))}\n"
                if comm_qa:
                    context_text += "Các câu Hỏi & Đáp:\n"
                    for q in comm_qa:
                        context_text += f"- Câu hỏi: {q['body']}\n  Tags: {', '.join(q.get('tags', []))}\n"
                        
        except Exception as e:
            print(f"[community_search] error: {e}")
            
    # 3. Tạo prompt và gọi LLM
    prompt = ChatPromptTemplate.from_template("""
Bạn là trợ lý thông minh. Hãy trả lời câu hỏi dựa trên thông tin trong lịch sử hội thoại và tài liệu được cung cấp.

=== QUY TẮC TRẢ LỜI ===
1. Nếu có thông tin từ "NỘI DUNG TÀI LIỆU (FILE IMPORT)", hãy ưu tiên dùng nó làm căn cứ chính.
2. Nếu không có trong file import nhưng có trong "TÀI LIỆU TỪ CỘNG ĐỒNG", hãy trả lời dựa trên đó và nêu rõ đây là thông tin từ cộng đồng.
3. Nếu người dùng hỏi về các chủ đề/tổng hợp mà không tìm thấy kết quả chính xác, hãy dùng các "Tags" từ tài liệu cộng đồng để gợi ý các chủ đề liên quan.
4. Nếu cả hai nguồn đều không có thông tin phù hợp, hãy thông báo: "Hiện tại hệ thống và cộng đồng chưa có thông tin chi tiết về vấn đề này." và gợi ý người dùng thử tìm kiếm bằng các từ khóa khác.
5. Luôn ưu tiên sự hữu ích và tính gợi mở.

=== LỊCH SỬ HỘI THOẠI GẦN ĐÂY ===
{history}

=== NỘI DUNG CHI TIẾT ===
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