import re


def compute_confidence(docs, customer, incidents, escalation, ticket_id):
    if docs:
        top_scores = [d["relevance"] for d in docs[:3]]
        avg = sum(top_scores) / len(top_scores)
        base = round(0.55 + avg * 0.40, 2)  # scales from 0.55 to 0.95
    elif incidents:
        base = 0.90  # live incident data is high-signal
    else:
        base = 0.55

    if customer:
        base = min(base + 0.03, 0.99)
    if escalation and ticket_id:
        base = min(base + 0.05, 0.99)

    return round(base, 2)


from app.tools.tools import (
    tool_get_customer,
    tool_get_plan,
    tool_get_incidents,
    tool_create_ticket,
    tool_search_docs,
)
from app.llm import llm


SECURITY_TERMS = [
    "ignore previous instructions",
    "ignore your previous",
    "all customers",
    "all enterprise",
    "api keys for all",
    "api keys",
    "enterprise customer details",
    "show all users",
    "customer secrets",
    "reveal all",
    "disregard previous",
]

CATEGORY_MAP = {
    "refund": "billing",
    "export": "exports",
    "sso": "authentication",
    "webhook": "integrations",
    "incident": "dashboard",
    "feature_check": None,
    "general": None,
}


def route_query(state):
    return state["route"]


def classify_node(state):
    query = state["query"].lower()
    trace = state.get("execution_trace") or []

    for term in SECURITY_TERMS:
        if term in query:
            state["route"] = "security"
            state["escalation"] = True
            state["escalation_reason"] = "Potential unauthorized data access or prompt injection attempt"
            trace.append("Security threat detected — rejecting")
            state["execution_trace"] = trace
            return state

    meaningful_keywords = [
        "sso", "saml", "scim", "export", "csv", "webhook",
        "dashboard", "refund", "rows", "outage", "region",
        "login", "upgrade", "plan", "billing", "audit", "slow"
    ]
    if len(query.strip()) < 25 and not any(k in query for k in meaningful_keywords):
        state["route"] = "ambiguous"
        state["escalation"] = True
        state["escalation_reason"] = "Query too ambiguous to determine the issue"
        trace.append("Query too vague — escalating for clarification")
        state["execution_trace"] = trace
        return state

    if "refund" in query:
        policy_words = ["will i get", "do i get", "would i get", "downgrade", "refund policy", "refund if", "am i eligible"]
        if any(k in query for k in policy_words):
            state["route"] = "general"
            trace.append("Classified intent: refund policy question (informational)")
        else:
            state["route"] = "refund"
            trace.append("Classified intent: refund request — requires escalation")

    elif any(k in query for k in ["dashboard", "outage", "affecting my region", "is there an outage"]):
        state["route"] = "incident"
        trace.append("Classified intent: incident/outage check")

    elif any(k in query for k in ["export", "csv", "fd-4297", "rows", "export scheduler"]):
        state["route"] = "export"
        trace.append("Classified intent: CSV export issue")

    elif any(k in query for k in ["sso", "saml", "scim", "single sign"]):
        state["route"] = "sso"
        trace.append("Classified intent: SSO/SCIM configuration")

    elif "webhook" in query:
        state["route"] = "webhook"
        trace.append("Classified intent: webhook troubleshooting")

    elif any(k in query for k in ["can my plan", "does my plan", "my current plan", "audit log", "audit-log"]):
        state["route"] = "feature_check"
        trace.append("Classified intent: plan/feature check")

    else:
        state["route"] = "general"
        trace.append("Classified intent: general query")

    state["execution_trace"] = trace
    return state


def customer_node(state):
    trace = state.get("execution_trace") or []
    tools = state.get("tools_used") or []

    customer = tool_get_customer(state["customer_id"])

    if not customer:
        tools.append({"tool": "get_customer", "status": "not_found"})
        state["escalation"] = True
        state["escalation_reason"] = f"Customer {state['customer_id']} not found"
        state["route"] = "ambiguous"
        trace.append(f"Customer {state['customer_id']} not found — escalating")
        state["execution_trace"] = trace
        state["tools_used"] = tools
        return state

    tools.append({"tool": "get_customer", "status": "success"})

    if customer.get("status") == "suspended":
        state["customer"] = customer
        state["escalation"] = True
        state["escalation_reason"] = "Customer account is suspended"
        state["route"] = "ambiguous"
        trace.append(f"Account {customer['company_name']} is suspended — escalating")
        state["execution_trace"] = trace
        state["tools_used"] = tools
        return state

    state["customer"] = customer
    state["plan"] = tool_get_plan(customer["plan"])
    trace.append(f"Fetched customer {customer['company_name']} (plan={customer['plan']}, version={customer['product_version']}, region={customer['region']})")
    state["execution_trace"] = trace
    state["tools_used"] = tools
    return state


def rag_node(state):
    trace = state.get("execution_trace") or []
    tools = state.get("tools_used") or []

    route = state.get("route", "general")
    customer = state.get("customer")

    version = None
    if customer:
        v = customer.get("product_version", "")
        if v and v[0] == "2":
            version = "2.x"
        elif v and v[0] == "3":
            version = "3.x"

    category = CATEGORY_MAP.get(route)
    result = tool_search_docs(state["query"], version=version, category=category)

    docs = result["docs"]
    adversarial = result["adversarial_detected"]

    tools.append({
        "tool": "search_docs",
        "status": "success",
        "citations": [f"{d['source']}#{d['section']}" for d in docs]
    })

    state["docs"] = docs
    state["citations"] = [
        {"source": d["source"], "section": d["section"], "relevance": d["relevance"]}
        for d in docs
    ]

    if adversarial:
        state["escalation"] = True
        state["escalation_reason"] = "Retrieved content contains potential system-override instructions"
        state["route"] = "security"
        trace.append("Adversarial content detected in retrieved docs — blocking")
    else:
        trace.append(f"Retrieved {len(docs)} docs (version={version}, category={category})")

    state["execution_trace"] = trace
    state["tools_used"] = tools
    return state


def incident_node(state):
    trace = state.get("execution_trace") or []
    tools = state.get("tools_used") or []

    customer = state.get("customer")
    if not customer:
        state["incidents"] = []
        return state

    incidents = tool_get_incidents(customer["region"])
    tools.append({"tool": "get_incidents", "status": "success"})
    state["incidents"] = incidents

    if incidents:
        titles = [i["title"] for i in incidents]
        trace.append(f"Found {len(incidents)} active incident(s) in {customer['region']}: {titles}")
    else:
        trace.append(f"No active incidents in {customer['region']}")

    state["execution_trace"] = trace
    state["tools_used"] = tools
    return state


def refund_node(state):
    trace = state.get("execution_trace") or []
    tools = state.get("tools_used") or []

    customer_id = state["customer_id"]
    idempotency_key = f"{customer_id}_refund_{state['query'][:40].replace(' ', '_')}"

    ticket = tool_create_ticket(
        customer_id=customer_id,
        category="billing",
        priority="medium",
        summary=f"Refund request: {state['query'][:100]}",
        assigned_team="billing-support",
        evidence=[state["query"]],
        idempotency_key=idempotency_key,
        status="pending_approval",
    )

    tools.append({"tool": "create_ticket", "status": "success" if ticket else "error"})
    state["ticket_id"] = ticket["ticket_id"] if ticket else None
    state["escalation"] = True
    state["escalation_reason"] = "Refund requests require manual review by billing-support"
    trace.append(f"Policy: AI must not process refunds — created ticket {ticket['ticket_id'] if ticket else 'N/A'}")
    state["execution_trace"] = trace
    state["tools_used"] = tools
    return state


def export_node(state):
    trace = state.get("execution_trace") or []

    plan = state.get("plan")
    customer = state.get("customer")
    limit = plan["limits"].get("csv_export_rows") if plan else None

    match = re.search(r"(\d[\d,]+)\s*rows?", state["query"].lower())
    row_count = int(match.group(1).replace(",", "")) if match else None

    if row_count and limit:
        if row_count > limit:
            trace.append(f"Row count {row_count:,} exceeds plan limit {limit:,} — providing workaround")
        else:
            trace.append(f"Row count {row_count:,} is within plan limit {limit:,}")
    elif limit:
        trace.append(f"Plan export limit is {limit:,} rows")

    if customer:
        v = customer.get("product_version", "")
        if "v3.2" in state["query"].lower() and not v.startswith("3.2"):
            trace.append(f"Version mismatch: customer is on v{v}, requested feature is v3.2 only")

    state["decision"] = f"Plan export limit: {limit} rows. Reported row count: {row_count or 'not specified'}."
    state["execution_trace"] = trace
    return state


def sso_node(state):
    trace = state.get("execution_trace") or []

    customer = state.get("customer")
    if not customer:
        state["decision"] = "Returning general SSO setup instructions"
        trace.append("No customer context — returning general SSO documentation")
        state["execution_trace"] = trace
        return state

    features = customer.get("features", {})
    saml_enabled = features.get("saml_sso", False)
    version = customer.get("product_version", "unknown")
    plan = customer.get("plan", "unknown")

    if not saml_enabled:
        state["decision"] = f"SAML SSO is disabled for this tenant (plan={plan}, version={version}). The feature flag saml_sso is off — may need admin re-enablement or plan upgrade."
        trace.append(f"SSO feature flag is disabled for {customer['company_name']} (v{version})")
    else:
        state["decision"] = f"SSO is enabled for this tenant (plan={plan}, version={version})."
        trace.append(f"SSO is enabled for {customer['company_name']} (v{version})")

    state["execution_trace"] = trace
    return state


def webhook_node(state):
    trace = state.get("execution_trace") or []
    tools = state.get("tools_used") or []

    docs = state.get("docs", [])
    query = state.get("query", "").lower()
    customer = state.get("customer")

    specific_terms = [
        "signature", "endpoint", "payload", "ssl", "timeout",
        "retry", "delivery", "error code", "403", "401", "500",
        "v3.2", "v3.1", "upgrade", "verification"
    ]
    has_specific_info = any(term in query for term in specific_terms)

    if not has_specific_info or not docs:
        state["escalation"] = True
        state["escalation_reason"] = "Insufficient diagnostic information to resolve webhook issue"
        trace.append("Webhook query lacks specific diagnostic info — escalating")

        customer_id = state["customer_id"]
        idempotency_key = f"{customer_id}_webhook_{query[:30].replace(' ', '_')}"
        ticket = tool_create_ticket(
            customer_id=customer_id,
            category="configuration",
            priority="medium",
            summary=f"Webhook issue: {state['query'][:100]}",
            assigned_team="technical-support",
            evidence=[state["query"]],
            idempotency_key=idempotency_key,
            status="pending_approval",
        )
        tools.append({"tool": "create_ticket", "status": "success" if ticket else "error"})
        state["ticket_id"] = ticket["ticket_id"] if ticket else None
        trace.append(f"Created escalation ticket {state['ticket_id']}")
    else:
        if customer:
            trace.append(f"Providing webhook troubleshooting for v{customer.get('product_version', '?')}")
        else:
            trace.append("Providing webhook troubleshooting documentation")

    state["execution_trace"] = trace
    state["tools_used"] = tools
    return state


def response_node(state):
    trace = state.get("execution_trace") or []
    tools = state.get("tools_used") or []

    route = state.get("route", "general")
    escalation = state.get("escalation", False)
    customer = state.get("customer")
    docs = state.get("docs") or []
    incidents = state.get("incidents") or []

    if route == "security" and not docs:
        answer = "This request has been identified as a potential security threat or unauthorized access attempt. The request has been blocked and flagged for review."
        confidence = 0.99
    else:
        doc_snippets = [f"[{d['source']} / {d['section']}]: {d['content'][:250]}" for d in docs[:3]]

        prompt = f"""You are a FlowDesk customer support assistant. Be concise and direct (2-4 sentences).

Customer info: {customer}
Query: {state.get("query")}
Decision context: {state.get("decision")}
Relevant documentation: {doc_snippets if doc_snippets else "None"}
Active incidents: {incidents if incidents else "None"}
Escalating to human: {escalation}
Escalation reason: {state.get("escalation_reason")}
Ticket created: {state.get("ticket_id")}

Write a helpful response. If escalating, tell the customer why and give them the ticket ID."""

        llm_response = llm.invoke(prompt)
        tools.append({"tool": "llm_response", "status": "success"})
        answer = llm_response.content

        confidence = compute_confidence(
            docs=docs,
            customer=customer,
            incidents=incidents,
            escalation=escalation,
            ticket_id=state.get("ticket_id"),
        )

    if route == "security":
        status = "rejected"
    elif escalation:
        status = "escalated"
    else:
        status = "resolved"

    trace.append(f"Generated response — status={status}, confidence={confidence}")
    state["answer"] = answer
    state["status"] = status
    state["confidence"] = confidence
    state["tools_used"] = tools
    state["execution_trace"] = trace
    return state
