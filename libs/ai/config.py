# src/config.py
import os
from dotenv import load_dotenv

load_dotenv()

LLM_BASE_URL = "https://api.groq.com/openai/v1"
LLM_API_KEY  = os.getenv("GROQ_API_KEY")
LLM_MODEL    = "llama-3.3-70b-versatile"

LLM_TEMPERATURE = 0.2

# === Token Control ===
MAX_OUTPUT_TOKENS   = 512
CONTEXT_TOKEN_LIMIT = 3000
CHARS_PER_TOKEN     = 4

# === Embedding ===
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

# === Vector Store ===
VECTORSTORE_DIR = "vectorstore"
COLLECTION_NAME = "documents"

# === Chunking ===
CHUNK_SIZE    = 2000
CHUNK_OVERLAP = 200

# === Retrieval ===
TOP_K = 6

# === Reranking ===
RERANKER_MODEL   = "cross-encoder/msmarco-MiniLM-L6-en-de-v1"
RERANK_TOP_K     = 3
RERANK_THRESHOLD = -5.0