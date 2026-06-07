from langchain_groq import ChatGroq
from app.config import GROQ_API_KEY, LLM_MODEL

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env file")

llm = ChatGroq(
    model=LLM_MODEL,
    api_key=GROQ_API_KEY,
    temperature=0
)