from typing import TypedDict, Optional


class AgentState(TypedDict):
    customer_id: str
    query: str

    customer: Optional[dict]
    plan: Optional[dict]

    docs: Optional[list]
    incidents: Optional[list]

    route: Optional[str]
    decision: Optional[str]
    answer: Optional[str]

    # escalation
    escalation: bool
    escalation_reason: Optional[str]

    # ticket
    ticket_id: Optional[str]

    # structured output fields
    status: Optional[str]           # "resolved" | "escalated" | "rejected"
    confidence: Optional[float]     # 0.0 – 1.0
    tools_used: Optional[list]      # [{"tool": str, "status": str, "latency_ms": int}]
    execution_trace: Optional[list] # ["step description", ...]
    citations: Optional[list]       # [{"source": str, "section": str, "relevance": float}]