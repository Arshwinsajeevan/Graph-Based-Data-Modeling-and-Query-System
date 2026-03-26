# Dodge AI — Graph-Based Context System

A full-stack LLM-powered interface for analyzing SAP Order-to-Cash data via a graph visualization and conversational AI.

> **Take-home assignment for Dodge AI FDE role.**

---

## Live Demo

| Service  | URL |
|----------|-----|
| Frontend | `http://localhost:5173` |
| Backend  | `http://localhost:8000` |

---

## Quick Start

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Add your Groq API key
copy .env.example .env
# Edit .env → GROQ_API_KEY=your_key_here

# Start server (auto-seeds DB on first run)
uvicorn main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**

---

## Architecture

```
React Frontend (Vite)
  ├── GraphView (react-force-graph-2d)
  └── ChatPanel  ──POST /chat──▶  FastAPI Backend
                                    ├── Guardrails (keyword check)
                                    ├── Groq LLM (NL → SQL)
                                    ├── SQLite (execute SQL)
                                    └── Groq LLM (SQL results → answer)
```

**Key decisions:**

| Decision | Why |
|----------|-----|
| SQLite | Zero-setup, single file, perfect for a bounded dataset |
| Dual table design | Raw relational tables for SQL + flattened graph tables for visualization |
| Two-step LLM pipeline | NL→SQL is deterministic (temp=0); answer generation is separate (prevents hallucination) |
| Groq + llama3-70b | Free tier, fast inference, strong SQL reasoning |
| react-force-graph-2d | Canvas-based, handles 500+ nodes without lag |

---

## LLM Strategy

**Step 1 — NL → SQL** (`temperature=0`)
- Full schema injected into system prompt
- Strict instructions: return ONLY raw SQL or `CANNOT_ANSWER`
- Shot-examples for the three target query types

**Step 2 — SQL Results → Answer** (`temperature=0.3`)
- Raw query results passed as context
- LLM grounded to data only — no hallucination possible
- Business language enforced (no SQL/DB jargon in response)

---

## Guardrails (3 Layers)

| Layer | Mechanism | Cost |
|-------|-----------|------|
| 1 | Keyword check (`guardrails.py`) | Zero — instant reject |
| 2 | System prompt instruction | Covered by existing call |
| 3 | SQL execution error catch | Zero — fallback message |

**Rejection message:** *"This system only answers questions related to the provided dataset (Order-to-Cash: sales orders, deliveries, billing documents, journal entries)."*

---

## Dataset

Sample SAP Order-to-Cash data covering:
- **10 Sales Orders** (customers + materials)
- **9 Deliveries** (linked to orders)
- **8 Billing Documents** (linked to deliveries)
- **8 Journal Entries** (linked to billing docs)

One delivery (DEL-2005) is intentionally left unbilled to demonstrate the "broken flow" query.

---

## Example Queries

| Query | What it tests |
|-------|--------------|
| "Which products have highest billing count?" | Aggregation + multi-table join |
| "Trace flow of billing document 91150187" | Document tracing across 4 tables |
| "Find broken flows (delivered but not billed)" | LEFT JOIN gap detection |
| "What is 2+2?" | Guardrail rejection |

---

## Tradeoffs

| Tradeoff | Decision |
|----------|----------|
| Graph DB vs SQLite | Chose SQLite — simpler, no extra infra, sufficient for O2C scale |
| Vector similarity guardrail vs keywords | Chose keywords — zero latency, no extra API call |
| Streaming responses | Skipped — adds complexity, not critical for this use case |
| Authentication | Skipped — out of scope for 1-day build |
