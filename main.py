import logging

from fastapi import FastAPI

from app.api.routes import router

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO
)

app = FastAPI(
    title="FlowDesk Support Agent",
    version="1.0.0",
    description="Agentic AI customer support system for FlowDesk SaaS"
)


@app.get("/health")
def health_check():
    import sqlite3
    import os
    from app.config import DB_PATH, CHROMA_DIR

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("SELECT 1").fetchone()
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    chroma_ok = os.path.exists(CHROMA_DIR)

    return {
        "status": "healthy" if db_ok and chroma_ok else "degraded",
        "database": "ok" if db_ok else "error",
        "vector_store": "ok" if chroma_ok else "missing",
    }


app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
