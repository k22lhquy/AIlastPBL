"""
BM25 Retriever + Reciprocal Rank Fusion (RRF)

Module này cung cấp:
- Tìm kiếm từ khóa dùng BM25 (TF-IDF nâng cao)
- Gộp kết quả BM25 + Vector bằng Reciprocal Rank Fusion
"""

import re
from typing import List, Tuple, Dict, Any
from rank_bm25 import BM25Okapi


def _simple_tokenize(text: str) -> List[str]:
    """
    Tokenizer đơn giản: lowercase + tách theo khoảng trắng + ký tự đặc biệt.
    Phù hợp với tiếng Việt (không cần word segmentation phức tạp vì BM25 hoạt động
    tốt ở cấp độ unigram với tiếng Việt).
    """
    text = text.lower()
    # Giữ lại chữ cái, số, dấu tiếng Việt
    text = re.sub(r'[^\w\s]', ' ', text, flags=re.UNICODE)
    tokens = text.split()
    return [t for t in tokens if len(t) > 1]  # Bỏ ký tự đơn lẻ


def build_bm25(chunks: List[Dict[str, Any]]) -> Tuple[BM25Okapi, List[Dict]]:
    """
    Xây dựng BM25 index từ danh sách chunks.
    
    Args:
        chunks: List các dict có key 'content', 'fileId'
        
    Returns:
        (bm25_model, filtered_chunks) — chỉ trả về chunks có content
    """
    valid_chunks = [c for c in chunks if c.get("content")]
    corpus = [_simple_tokenize(c["content"]) for c in valid_chunks]
    
    # Tránh crash nếu corpus rỗng
    if not corpus:
        return None, []
    
    bm25 = BM25Okapi(corpus)
    return bm25, valid_chunks


def bm25_search(
    bm25: BM25Okapi,
    chunks: List[Dict],
    query: str,
    top_k: int = 10
) -> List[Tuple[float, str, str]]:
    """
    Tìm kiếm BM25 cho 1 query.
    
    Returns:
        List of (score, content, fileId) — đã sort descending theo score
    """
    if bm25 is None or not chunks:
        return []
    
    tokens = _simple_tokenize(query)
    if not tokens:
        return []
    
    scores = bm25.get_scores(tokens)
    
    scored = []
    for i, (score, chunk) in enumerate(zip(scores, chunks)):
        if score > 0:
            scored.append((float(score), chunk.get("content", ""), chunk.get("fileId", "")))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]


def reciprocal_rank_fusion(
    vector_results: List[Tuple[float, str, str]],
    bm25_results: List[Tuple[float, str, str]],
    k: int = 60
) -> List[Tuple[float, str, str]]:
    """
    Gộp kết quả Vector Search và BM25 Search bằng Reciprocal Rank Fusion.
    
    RRF score(d) = Σ [ 1 / (k + rank_i(d)) ]
    
    Args:
        vector_results: List (score, content, fileId) từ Vector search
        bm25_results:   List (score, content, fileId) từ BM25 search
        k: Hằng số RRF (mặc định 60 — theo bài báo gốc)
        
    Returns:
        List (rrf_score, content, fileId) sorted descending
    """
    rrf_scores: Dict[str, float] = {}
    content_map: Dict[str, Tuple[str, str]] = {}  # key -> (content, fileId)
    
    def _key(content: str) -> str:
        # Dùng 120 ký tự đầu làm key nhận dạng chunk
        return content[:120].strip()
    
    # Tính RRF từ Vector search
    for rank, (score, content, file_id) in enumerate(vector_results, start=1):
        key = _key(content)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
        content_map[key] = (content, file_id)
    
    # Tính RRF từ BM25 search
    for rank, (score, content, file_id) in enumerate(bm25_results, start=1):
        key = _key(content)
        rrf_scores[key] = rrf_scores.get(key, 0.0) + 1.0 / (k + rank)
        if key not in content_map:
            content_map[key] = (content, file_id)
    
    # Sort descending theo RRF score
    sorted_keys = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    
    result = []
    for key, rrf_score in sorted_keys:
        content, file_id = content_map[key]
        result.append((rrf_score, content, file_id))
    
    return result
