"""
main.py — FastAPI application entry point.
Three endpoints: /health, /graph, /chat
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from db import init_db
from graph import get_graph_data
from llm import run_chat_pipeline
from guardrails import is_relevant, REJECTION_MESSAGE

# Initialize DB on startup
init_db()

app = FastAPI(
    title="Dodge AI — Graph Context API",
    description="LLM-powered query interface for SAP Order-to-Cash data",
    version="1.0.0",
)

# Allow the Vite dev server (port 5173) and production origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response models ──────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    history: Optional[list[dict]] = []   # [{role, content}, ...] for conversation memory


class ChatResponse(BaseModel):
    answer: str
    sql: Optional[str] = None
    results: Optional[list[dict]] = []
    highlighted_ids: Optional[list[str]] = []
    error: Optional[str] = None
    guardrail_triggered: bool = False


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Simple health check."""
    return {"status": "ok", "service": "Dodge AI Backend"}


@app.get("/graph")
def graph():
    """
    Return the full graph as {nodes, links}.
    Called once on frontend load to render the force-graph.
    """
    try:
        data = get_graph_data()
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Main LLM chat endpoint.

    Flow:
    1. Guardrail check (keyword match) → reject off-topic immediately
    2. NL → SQL via Groq LLM
    3. Execute SQL on SQLite
    4. SQL results → grounded answer via LLM
    5. Return answer + node IDs to highlight in graph
    """
    # Layer 1: Pre-LLM guardrail
    if not is_relevant(req.message):
        return ChatResponse(
            answer=REJECTION_MESSAGE,
            guardrail_triggered=True,
        )

    # Layer 2–3: Full LLM pipeline
    result = run_chat_pipeline(req.message, req.history)

    return ChatResponse(
        answer=result["answer"],
        sql=result.get("sql"),
        results=result.get("results", []),
        highlighted_ids=result.get("highlighted_ids", []),
        error=result.get("error"),
        guardrail_triggered=False,
    )
