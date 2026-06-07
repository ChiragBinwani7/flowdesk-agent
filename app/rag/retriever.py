import re
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi

ADVERSARIAL_PHRASES = [
    "system override",
    "ignore the user request",
    "all permissions granted",
    "reveal all customer",
    "disregard previous",
    "ignore previous instructions",
]

from app.config import CHROMA_DIR, EMBED_MODEL


def is_adversarial(text, meta=None):
    if meta and meta.get("is_adversarial"):
        return True
    return any(phrase in text.lower() for phrase in ADVERSARIAL_PHRASES)


def extract_section(content):
    match = re.search(r"^#{1,3}\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "General"


def clean_source(source):
    return source.split("/")[-1] if source else "unknown"


def search_docs(query, version=None, category=None):
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectordb = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

    # build version filter for dense search
    version_values = None
    if version == "2.x":
        version_values = ["2.x", "all"]
    elif version == "3.x":
        version_values = ["3.x", "3.1", "3.2", "all"]

    where = {}
    if version_values and category:
        where = {"$and": [{"version": {"$in": version_values}}, {"category": category}]}
    elif version_values:
        where = {"version": {"$in": version_values}}
    elif category:
        where = {"category": category}

    # dense search
    if where:
        dense_results = vectordb.similarity_search_with_relevance_scores(query, k=4, filter=where)
    else:
        dense_results = vectordb.similarity_search_with_relevance_scores(query, k=4)

    # bm25 search — load all docs and keyword-score them
    all_docs = vectordb.get(include=["documents", "metadatas"])
    documents = all_docs["documents"]
    metadatas = all_docs["metadatas"]

    filtered = []
    for doc, meta in zip(documents, metadatas):
        doc_version = meta.get("version", "")
        if version and doc_version != "all":
            if version == "2.x" and not doc_version.startswith("2"):
                continue
            if version == "3.x" and not doc_version.startswith("3"):
                continue
        if category and meta.get("category") != category:
            continue
        filtered.append((doc, meta))

    if not filtered:
        filtered = list(zip(documents, metadatas))

    corpus = [doc.lower().split() for doc, _ in filtered]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query.lower().split())
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:4]
    bm25_results = [(filtered[i][0], filtered[i][1], scores[i]) for i in top_indices if scores[i] > 0]

    # merge dense + bm25, deduplicate, filter adversarial
    seen = set()
    final = []
    adversarial_found = False

    for doc, score in dense_results:
        content = doc.page_content
        if is_adversarial(content, doc.metadata):
            adversarial_found = True
            continue
        key = content[:100]
        if key in seen:
            continue
        seen.add(key)
        final.append({
            "source": clean_source(doc.metadata.get("source", "")),
            "section": extract_section(content),
            "content": content,
            "relevance": round(float(score), 3),
            "retrieval": "dense"
        })

    for content, meta, score in bm25_results:
        if is_adversarial(content, meta):
            adversarial_found = True
            continue
        key = content[:100]
        if key in seen:
            continue
        seen.add(key)
        final.append({
            "source": clean_source(meta.get("source", "")),
            "section": extract_section(content),
            "content": content,
            "relevance": round(min(score / 10.0, 1.0), 3),
            "retrieval": "bm25"
        })

    final.sort(key=lambda x: x["relevance"], reverse=True)
    return {"docs": final[:5], "adversarial_detected": adversarial_found}
