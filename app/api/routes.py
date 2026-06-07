import json
import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from app.db.sqlite_manager import get_connection, get_customer, get_plan, get_incidents, get_tickets, create_ticket, approve_ticket, reject_ticket, save_trace, get_traces
from app.graph.graph import graph

router = APIRouter()
logger = logging.getLogger(__name__)


class TicketRequest(BaseModel):
    customer_id: str
    category: str
    priority: str
    summary: str
    assigned_team: str
    evidence: list = []
    idempotency_key: Optional[str] = None


class SupportQueryRequest(BaseModel):
    customer_id: str
    query: str


@router.get("/customers/{customer_id}")
def get_customer_route(customer_id: str):
    customer = get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    return customer


@router.get("/plans/{plan_name}")
def get_plan_route(plan_name: str):
    plan = get_plan(plan_name)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{plan_name}' not found")
    return plan


@router.get("/incidents")
def get_incidents_route(
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="active (default) or all"),
):
    conn = get_connection()

    if status == "all":
        sql = "SELECT * FROM incidents"
        params = []
        if region:
            sql += " WHERE region = ? OR region = 'global'"
            params = [region]
    else:
        sql = "SELECT * FROM incidents WHERE status IN ('investigating', 'identified', 'monitoring')"
        params = []
        if region:
            sql += " AND (region = ? OR region = 'global')"
            params = [region]

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    incidents = []
    for row in rows:
        inc = dict(row)
        if inc.get("affects_plans"):
            inc["affects_plans"] = json.loads(inc["affects_plans"])
        incidents.append(inc)

    return {"incidents": incidents, "count": len(incidents)}


@router.get("/tickets")
def list_tickets_route():
    return {"tickets": get_tickets()}


@router.post("/tickets", status_code=201)
def create_ticket_route(req: TicketRequest):
    return create_ticket(
        customer_id=req.customer_id,
        category=req.category,
        priority=req.priority,
        summary=req.summary,
        assigned_team=req.assigned_team,
        evidence=req.evidence,
        idempotency_key=req.idempotency_key,
    )


@router.post("/tickets/{ticket_id}/approve")
def approve_ticket_route(ticket_id: str):
    approve_ticket(ticket_id)
    return {"ticket_id": ticket_id, "status": "approved"}


@router.post("/tickets/{ticket_id}/reject")
def reject_ticket_route(ticket_id: str):
    reject_ticket(ticket_id)
    return {"ticket_id": ticket_id, "status": "rejected"}


@router.get("/traces")
def get_traces_route(limit: int = Query(50)):
    return {"traces": get_traces(limit=limit)}


@router.get("/kb/search")
def kb_search_route(
    q: str = Query(...),
    category: Optional[str] = Query(None),
    version: Optional[str] = Query(None),
):
    conn = get_connection()
    like = f"%{q.lower()}%"
    sql = """
        SELECT doc_id, title, source_file, category, product_version, section
        FROM kb_documents
        WHERE is_adversarial = 0
          AND (LOWER(title) LIKE ? OR LOWER(content) LIKE ? OR LOWER(section) LIKE ?)
    """
    params = [like, like, like]

    if category:
        sql += " AND category = ?"
        params.append(category)
    if version:
        sql += " AND (product_version = ? OR product_version = 'all')"
        params.append(version)

    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return {"results": [dict(row) for row in rows], "count": len(rows), "query": q}


@router.get("/diagnostics/{customer_id}")
def run_diagnostic_route(
    customer_id: str,
    check: Optional[str] = Query(None, description="export | auth | webhook | dashboard"),
):
    customer = get_customer(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    features = customer.get("features", {})
    limits = customer.get("limits", {})
    region = customer.get("region")
    run_all = check is None
    checks = {}

    if run_all or check == "export":
        enabled = features.get("csv_export", False)
        checks["export_health"] = {
            "status": "healthy" if enabled else "disabled",
            "csv_export_enabled": enabled,
            "row_limit": limits.get("csv_export_rows", 0),
            "latency_ms": 12,
        }

    if run_all or check == "auth":
        sso = features.get("saml_sso", False)
        checks["auth_config"] = {
            "status": "configured" if sso else "not_configured",
            "saml_sso": sso,
            "scim": features.get("scim", False),
            "latency_ms": 8,
        }

    if run_all or check == "webhook":
        wh = features.get("webhooks", False)
        checks["webhook_health"] = {
            "status": "healthy" if wh else "disabled",
            "webhooks_enabled": wh,
            "latency_ms": 15,
        }

    if run_all or check == "dashboard":
        active = get_incidents(region)
        checks["dashboard_latency"] = {
            "status": "degraded" if active else "healthy",
            "active_incidents": len(active),
            "region": region,
            "latency_ms": 45 if active else 180,
        }

    return {"customer_id": customer_id, "company": customer["company_name"], "checks": checks}


@router.post("/support/query")
def support_query_route(req: SupportQueryRequest, request: Request):
    if not req.customer_id.strip():
        raise HTTPException(status_code=400, detail="customer_id cannot be empty")
    if len(req.query.strip()) < 3:
        raise HTTPException(status_code=400, detail="query must be at least 3 characters long")

    request_id = getattr(request.state, "request_id", "unknown")
    t0 = time.time()
    logger.info(f"[{request_id}] {req.customer_id} — {req.query[:60]}")

    result = graph.invoke({
        "customer_id": req.customer_id,
        "query": req.query,
        "customer": None,
        "plan": None,
        "docs": None,
        "incidents": None,
        "route": None,
        "decision": None,
        "answer": None,
        "escalation": False,
        "escalation_reason": None,
        "ticket_id": None,
        "status": None,
        "confidence": None,
        "tools_used": [],
        "execution_trace": [],
        "citations": [],
    })

    elapsed = int((time.time() - t0) * 1000)
    logger.info(f"[{request_id}] done — status={result.get('status')}, confidence={result.get('confidence')}, {elapsed}ms")

    save_trace(
        request_id=request_id,
        customer_id=req.customer_id,
        query=req.query,
        status=result.get("status"),
        confidence=result.get("confidence"),
        tools_used=[t["tool"] for t in result.get("tools_used", [])],
        latency_ms=elapsed,
        escalation=result.get("escalation", False),
        execution_trace=result.get("execution_trace", []),
    )

    return {
        "ticket_id": result.get("ticket_id"),
        "customer_id": req.customer_id,
        "status": result.get("status", "resolved"),
        "answer": result.get("answer", ""),
        "confidence": result.get("confidence", 0.0),
        "escalation_required": result.get("escalation", False),
        "escalation_reason": result.get("escalation_reason"),
        "tools_used": result.get("tools_used", []),
        "execution_trace": result.get("execution_trace", []),
        "citations": result.get("citations", []),
        "total_latency_ms": elapsed,
    }
