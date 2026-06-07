from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

from app.config import CHROMA_DIR, EMBED_MODEL

DOCS_DIR = "data/docs"

# metadata per file — version and category for filtering
FILE_METADATA = {
    "sso-setup-v2.md":           {"version": "2.x", "category": "authentication", "is_adversarial": False},
    "sso-setup-v3.md":           {"version": "3.x", "category": "authentication", "is_adversarial": False},
    "export-limits-v2.md":       {"version": "2.x", "category": "exports",        "is_adversarial": False},
    "export-limits-v3.md":       {"version": "3.x", "category": "exports",        "is_adversarial": False},
    "webhook-troubleshooting.md":{"version": "all", "category": "integrations",   "is_adversarial": False},
    "billing-refund-policy.md":  {"version": "all", "category": "billing",        "is_adversarial": False},
    "dashboard-known-issues.md": {"version": "all", "category": "dashboard",      "is_adversarial": False},
    "release-notes-v3.1.md":     {"version": "3.1", "category": "release-notes",  "is_adversarial": False},
    "release-notes-v3.2.md":     {"version": "3.2", "category": "release-notes",  "is_adversarial": False},
    "system-override.md":        {"version": "all", "category": "system",         "is_adversarial": True},
}


def ingest_docs():
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    all_chunks = []

    for filename, meta in FILE_METADATA.items():
        filepath = os.path.join(DOCS_DIR, filename)

        if not os.path.exists(filepath):
            print(f"SKIP (not found): {filename}")
            continue

        loader = TextLoader(filepath)
        docs = loader.load()
        chunks = splitter.split_documents(docs)

        # attach metadata to every chunk from this file
        for chunk in chunks:
            chunk.metadata["source"] = filename
            chunk.metadata["version"] = meta["version"]
            chunk.metadata["category"] = meta["category"]
            chunk.metadata["is_adversarial"] = meta["is_adversarial"]

        all_chunks.extend(chunks)
        print(f"Loaded {filename} → {len(chunks)} chunks")

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)

    Chroma.from_documents(
        documents=all_chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )

    print(f"\nTotal chunks ingested: {len(all_chunks)}")


if __name__ == "__main__":
    ingest_docs()
