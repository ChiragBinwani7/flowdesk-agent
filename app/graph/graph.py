from langgraph.graph import StateGraph, END

from app.graph.state import AgentState
from app.graph.nodes import (
    classify_node,
    customer_node,
    rag_node,
    incident_node,
    refund_node,
    export_node,
    sso_node,
    webhook_node,
    response_node,
    route_query,
)


builder = StateGraph(AgentState)

builder.add_node("classify",  classify_node)
builder.add_node("customer",  customer_node)
builder.add_node("rag",       rag_node)
builder.add_node("incident",  incident_node)
builder.add_node("refund",    refund_node)
builder.add_node("export",    export_node)
builder.add_node("sso",       sso_node)
builder.add_node("webhook",   webhook_node)
builder.add_node("response",  response_node)

builder.set_entry_point("classify")

# after classify:
#   security / ambiguous → response immediately (no DB calls)
#   everything else      → fetch customer first
builder.add_conditional_edges(
    "classify",
    route_query,
    {
        "security":     "response",
        "ambiguous":    "response",
        "incident":     "customer",
        "refund":       "customer",
        "export":       "customer",
        "sso":          "customer",
        "webhook":      "customer",
        "feature_check":"customer",
        "general":      "customer",
    }
)

# after customer:
#   suspended / not-found → response immediately
#   incident              → fetch incidents (skip RAG for now, incident_node adds context)
#   everything else       → RAG
builder.add_conditional_edges(
    "customer",
    route_query,
    {
        "ambiguous":    "response",
        "incident":     "incident",
        "refund":       "rag",
        "export":       "rag",
        "sso":          "rag",
        "webhook":      "rag",
        "feature_check":"rag",
        "general":      "rag",
    }
)

# incident → response
builder.add_edge("incident", "response")

# after RAG:
#   adversarial detected → security → response
#   each intent          → its own node
#   feature_check/general → response directly (LLM handles it)
builder.add_conditional_edges(
    "rag",
    route_query,
    {
        "security":     "response",
        "refund":       "refund",
        "export":       "export",
        "sso":          "sso",
        "webhook":      "webhook",
        "feature_check":"response",
        "general":      "response",
    }
)

# specific nodes → response
builder.add_edge("refund",  "response")
builder.add_edge("export",  "response")
builder.add_edge("sso",     "response")
builder.add_edge("webhook", "response")

builder.add_edge("response", END)

graph = builder.compile()
