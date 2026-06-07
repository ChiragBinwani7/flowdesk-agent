# FlowDesk Support Agent

An agentic AI system that receives customer support queries and attempts to resolve them autonomously. It uses LangGraph to orchestrate multi-step workflows, ChromaDB for document retrieval, Groq (Llama 3.3 70B) as the LLM, and SQLite as the backend database.

The system does not call all tools for every query. It classifies the intent first, then selects only the tools actually needed — a refund query never touches the incidents table, a documentation question skips ticket creation entirely.

---

## How to run

Make sure you have `uv` installed, then from the `flowdesk-agent` folder:

```
uv sync
```

Copy your Groq API key into `.env`:

```
GROQ_API_KEY=your_key_here
```

Ingest the product documentation into ChromaDB (only needed once):

```
uv run python -m app.rag.ingest
```

Start the API server:

```
uv run uvicorn main:app --port 8001 --reload
```

Run the test suite:

```
uv run python tests/test_queries.py
```

---

## What the API exposes

Once the server is running, the main endpoint is:

```
POST /support/query
Body: { "customer_id": "cust_1024", "query": "Why is my CSV export failing?" }
```

The response includes the answer, whether escalation was needed, which tools were called, a step-by-step execution trace, and document citations.

There are also utility endpoints for looking up customers, plans, incidents, tickets, and searching the knowledge base directly. The full interactive docs are at `http://localhost:8001/docs`.

Tickets created by the agent for refund or webhook escalations are set to `pending_approval` status. A human can then act on them:

```
POST /tickets/{ticket_id}/approve
POST /tickets/{ticket_id}/reject
```

Every query is logged to a traces table in SQLite and viewable via:

```
GET /traces?limit=50
```

A health check is available at `GET /health`.

---

## Architecture

The core is a LangGraph state machine. When a query comes in, it flows through these nodes:

**classify** — reads the query and decides the intent. Security threats and completely vague queries are stopped here before any database calls happen.

**customer** — fetches the customer's account details from SQLite. If the account doesn't exist or is suspended, the flow short-circuits to escalation.

**rag** — searches the product documentation using a hybrid approach: dense vector search (ChromaDB + sentence-transformers) combined with BM25 keyword matching. Results are filtered by the customer's product version so a v2.x customer doesn't get v3.x instructions. Any chunk from `system-override.md` or containing known adversarial phrases is silently dropped before it reaches the LLM.

**intent-specific nodes** — after RAG, the query goes to whichever node fits the intent. The refund node creates a ticket and escalates. The export node compares the customer's row count against their plan limit. The SSO node checks whether the feature flag is actually enabled for that tenant. The webhook node escalates if the query lacks enough diagnostic information.

**response** — calls the LLM with all gathered context and produces the final answer.

---

## Design decisions

**Why keyword classification instead of LLM classification**

All 25 test queries contain obvious intent signals. Using an LLM to classify would add 500ms+ of latency and cost per request for no measurable improvement on this dataset. The classification logic is easy to read, easy to debug, and deterministic.

**Why call the customer API even for documentation questions**

The customer's product version is needed to filter the right docs. A v2.x customer asking about SSO should get v2.x instructions, not v3.x. Fetching the customer first is a small cost that meaningfully improves answer quality.

**Why hybrid retrieval**

Dense embeddings are good at semantic similarity but bad at exact matches like error codes (`FD-4297`) or specific version numbers. BM25 handles these well. The two approaches complement each other — results from both are merged, deduplicated, and sorted by relevance before reaching the LLM.

**Why idempotent tickets**

Support agents sometimes retry requests when they don't get an immediate response. Without idempotency keys, a customer asking for a refund twice would create two tickets. The key is derived from the customer ID and the first 40 characters of the query, so semantically identical requests don't duplicate.

**Why the adversarial document is handled at retrieval time, not prompt time**

Filtering in the prompt ("ignore any instructions telling you to...") can be bypassed through clever prompt injection. Filtering at the retrieval layer — before the content ever reaches the LLM — is more reliable. The `system-override.md` file is flagged with `is_adversarial=True` in its metadata at ingest time, so it is always excluded from results regardless of query.

---

## Running the tests

The test suite loads all 25 queries from `data/example-queries.json` and checks whether the agent's escalation decision matches the expected outcome. No test data is hardcoded — it all comes from the provided query file.

```
uv run python tests/test_queries.py
```

Current result: 25/25 passing.
