import os
from dotenv import load_dotenv

load_dotenv()

# Database
DB_PATH = os.getenv("DB_PATH", "data/flowdesk.db")

# RAG
CHROMA_DIR = os.getenv("CHROMA_DIR", "data/chroma_db")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# LLM
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# Retries — increase via env vars if needed
TOOL_RETRIES = int(os.getenv("TOOL_RETRIES", "3"))
RAG_RETRIES = int(os.getenv("RAG_RETRIES", "2"))
RETRY_BACKOFF_BASE = float(os.getenv("RETRY_BACKOFF_BASE", "0.3"))
