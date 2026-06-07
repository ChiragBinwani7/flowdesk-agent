import time
import random

from app.db.sqlite_manager import get_customer, get_plan, get_incidents, create_ticket
from app.rag.retriever import search_docs as _search_docs
from app.config import TOOL_RETRIES, RAG_RETRIES, RETRY_BACKOFF_BASE


def _backoff(attempt):
    # exponential backoff: 0.3s, 0.6s, 1.2s... plus small random jitter
    return (2 ** attempt) * RETRY_BACKOFF_BASE + random.uniform(0, 0.1)


def tool_get_customer(customer_id):
    for attempt in range(TOOL_RETRIES):
        try:
            return get_customer(customer_id)
        except Exception:
            if attempt < TOOL_RETRIES - 1:
                time.sleep(_backoff(attempt))
    return None


def tool_get_plan(plan_name):
    for attempt in range(TOOL_RETRIES):
        try:
            return get_plan(plan_name)
        except Exception:
            if attempt < TOOL_RETRIES - 1:
                time.sleep(_backoff(attempt))
    return None


def tool_get_incidents(region):
    for attempt in range(TOOL_RETRIES):
        try:
            return get_incidents(region) or []
        except Exception:
            if attempt < TOOL_RETRIES - 1:
                time.sleep(_backoff(attempt))
    return []


def tool_create_ticket(customer_id, category, priority, summary, assigned_team, evidence=None, idempotency_key=None, status="created"):
    for attempt in range(TOOL_RETRIES):
        try:
            return create_ticket(
                customer_id=customer_id,
                category=category,
                priority=priority,
                summary=summary,
                assigned_team=assigned_team,
                evidence=evidence,
                idempotency_key=idempotency_key,
                status=status,
            )
        except Exception:
            if attempt < TOOL_RETRIES - 1:
                time.sleep(_backoff(attempt))
    return None


def tool_search_docs(query, version=None, category=None):
    for attempt in range(RAG_RETRIES):
        try:
            result = _search_docs(query, version=version, category=category)
            if isinstance(result, dict) and "docs" in result:
                return result
        except Exception:
            if attempt < RAG_RETRIES - 1:
                time.sleep(_backoff(attempt))
    return {"docs": [], "adversarial_detected": False}
