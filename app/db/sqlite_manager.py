import sqlite3
import json
from datetime import datetime, timezone

from app.config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_customer(customer_id: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM customers WHERE customer_id = ?",
        (customer_id,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    customer = dict(row)
    customer["features"] = json.loads(customer["features"])
    customer["limits"] = json.loads(customer["limits"])
    return customer


def get_plan(plan_name: str):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM plans WHERE plan_name = ?",
        (plan_name,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    plan = dict(row)
    plan["features"] = json.loads(plan["features"])
    plan["limits"] = json.loads(plan["limits"])
    plan["restrictions"] = json.loads(plan["restrictions"])
    return plan


def get_incidents(region: str):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM incidents WHERE region = ? AND status != 'resolved'",
        (region,)
    ).fetchall()
    conn.close()
    incidents = []
    for row in rows:
        incident = dict(row)
        if incident["affects_plans"]:
            incident["affects_plans"] = json.loads(incident["affects_plans"])
        incidents.append(incident)
    return incidents


def get_tickets():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM tickets").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def create_ticket(
    customer_id: str,
    category: str,
    priority: str,
    summary: str,
    assigned_team: str,
    evidence: list = None,
    idempotency_key: str = None,
    status: str = "created",
):
    conn = get_connection()

    if idempotency_key:
        existing = conn.execute(
            "SELECT * FROM tickets WHERE idempotency_key = ?",
            (idempotency_key,)
        ).fetchone()
        if existing:
            conn.close()
            return dict(existing)

    last = conn.execute(
        "SELECT ticket_id FROM tickets ORDER BY ticket_id DESC LIMIT 1"
    ).fetchone()

    if last:
        last_num = int(last["ticket_id"].replace("TKT-", ""))
        ticket_id = f"TKT-{last_num + 1}"
    else:
        ticket_id = "TKT-1001"

    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    evidence_json = json.dumps(evidence or [])

    conn.execute(
        """
        INSERT INTO tickets
            (ticket_id, customer_id, category, priority, summary,
             evidence, status, assigned_team, created_at, idempotency_key)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (ticket_id, customer_id, category, priority, summary,
         evidence_json, status, assigned_team, created_at, idempotency_key)
    )
    conn.commit()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "customer_id": customer_id,
        "category": category,
        "priority": priority,
        "summary": summary,
        "evidence": evidence or [],
        "status": status,
        "assigned_team": assigned_team,
        "created_at": created_at,
        "idempotency_key": idempotency_key,
    }


def approve_ticket(ticket_id: str):
    conn = get_connection()
    conn.execute("UPDATE tickets SET status = 'approved' WHERE ticket_id = ?", (ticket_id,))
    conn.commit()
    conn.close()


def reject_ticket(ticket_id: str):
    conn = get_connection()
    conn.execute("UPDATE tickets SET status = 'rejected' WHERE ticket_id = ?", (ticket_id,))
    conn.commit()
    conn.close()


def create_traces_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id    TEXT,
            customer_id   TEXT,
            query         TEXT,
            status        TEXT,
            confidence    REAL,
            tools_used    TEXT,
            latency_ms    INTEGER,
            escalation    INTEGER,
            execution_trace TEXT,
            created_at    TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_trace(request_id, customer_id, query, status, confidence, tools_used, latency_ms, escalation, execution_trace):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO traces
            (request_id, customer_id, query, status, confidence,
             tools_used, latency_ms, escalation, execution_trace, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_id, customer_id, query, status, confidence,
            json.dumps(tools_used), latency_ms, int(escalation),
            json.dumps(execution_trace),
            datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
    )
    conn.commit()
    conn.close()


def get_traces(limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM traces ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    traces = []
    for row in rows:
        t = dict(row)
        t["tools_used"] = json.loads(t["tools_used"])
        t["execution_trace"] = json.loads(t["execution_trace"])
        traces.append(t)
    return traces


# create traces table on first import
create_traces_table()
