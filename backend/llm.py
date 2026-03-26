"""
llm.py — Groq API integration with two-step LLM pipeline.

Step 1: NL → SQL  (schema injected, strict instructions)
Step 2: SQL results → grounded natural language answer

Why two steps?
- Separating SQL generation from answer generation lets us validate
  the SQL before spending tokens on a final answer.
- It completely prevents hallucination: the LLM only sees real data.
"""

import os
import re
from groq import Groq
from dotenv import load_dotenv
from db import DB_SCHEMA, execute_query

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# STEP 1 PROMPT — NL → SQL
# ---------------------------------------------------------------------------
NL_TO_SQL_SYSTEM_PROMPT = f"""You are a SQL expert for an SAP Order-to-Cash system.
Your ONLY job is to convert a user's natural language question into a valid SQLite SELECT query.

DATABASE SCHEMA:
{DB_SCHEMA}

STRICT RULES:
1. Return ONLY the raw SQL query. No explanation, no markdown, no code fences.
2. Only write SELECT statements. Never INSERT, UPDATE, DELETE, or DROP.
3. Use exact table and column names from the schema above.
4. If the question cannot be answered with the given schema, return exactly: CANNOT_ANSWER
5. Always add LIMIT 50 unless the user asks for all records.
6. The question is always about Order-to-Cash business data. Do not answer anything else.
7. For "billing document" IDs, the format is BILL-XXXXXXXX (e.g. BILL-91150187).
8. For "journal entry" document numbers like 9400635958, look in journal_entries.id (JE-9400635958) or reference_document.

EXAMPLE:
User: "Which products have the highest billing count?"
SQL: SELECT so.material, COUNT(bd.id) as billing_count FROM sales_orders so JOIN deliveries d ON d.sales_order_id = so.id JOIN billing_documents bd ON bd.delivery_id = d.id GROUP BY so.material ORDER BY billing_count DESC LIMIT 10;

User: "Trace flow of billing document 91150187"
SQL: SELECT so.id as sales_order, d.id as delivery, bd.id as billing_document, je.id as journal_entry, so.customer, so.material, bd.amount, bd.status FROM sales_orders so JOIN deliveries d ON d.sales_order_id = so.id JOIN billing_documents bd ON bd.delivery_id = d.id LEFT JOIN journal_entries je ON je.billing_doc_id = bd.id WHERE bd.id = 'BILL-91150187' LIMIT 50;

User: "Find broken flows (delivered but not billed)"
SQL: SELECT d.id as delivery_id, d.sales_order_id, d.delivery_date, d.status FROM deliveries d LEFT JOIN billing_documents bd ON bd.delivery_id = d.id WHERE d.status = 'Delivered' AND bd.id IS NULL LIMIT 50;
"""

# ---------------------------------------------------------------------------
# STEP 2 PROMPT — SQL Results → Grounded Answer
# ---------------------------------------------------------------------------
ANSWER_SYSTEM_PROMPT = """You are Dodge AI, a graph agent for SAP Order-to-Cash data analysis.
You answer user questions using ONLY the data provided to you in the query results.

STRICT RULES:
1. Base your answer ONLY on the provided SQL results. Do not invent or assume any data.
2. Be concise and clear. Use bullet points or tables when helpful.
3. If the results are empty, say so clearly and suggest why.
4. Do NOT mention SQL, databases, or technical implementation details in your answer.
5. Speak in business terms: "sales orders", "billing documents", "deliveries", etc.
6. If the question is unrelated to Order-to-Cash, refuse politely.
7. Highlight key IDs or amounts using **bold**.
"""


def nl_to_sql(question: str) -> str | None:
    """
    Convert a natural language question to a SQL query using the LLM.
    Returns the SQL string, or None if the LLM says CANNOT_ANSWER.
    """
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,        # Deterministic output for SQL generation
        max_tokens=512,
        messages=[
            {"role": "system", "content": NL_TO_SQL_SYSTEM_PROMPT},
            {"role": "user",   "content": question},
        ],
    )
    sql = response.choices[0].message.content.strip()

    # Strip any accidental markdown fences the model might add
    sql = re.sub(r"```sql|```", "", sql).strip()

    if sql.upper() == "CANNOT_ANSWER" or not sql.upper().startswith("SELECT"):
        return None
    return sql


def generate_answer(question: str, sql_results: list[dict]) -> str:
    """
    Given the original question and SQL execution results,
    ask the LLM to produce a grounded, human-readable answer.
    """
    results_text = (
        str(sql_results[:20]) if sql_results
        else "No results found for this query."
    )

    user_message = f"""User question: {question}

SQL query results (raw data):
{results_text}

Please answer the user's question based solely on this data."""

    response = client.chat.completions.create(
        model=MODEL,
        temperature=0.3,
        max_tokens=1024,
        messages=[
            {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
    )
    return response.choices[0].message.content.strip()


def run_chat_pipeline(question: str, history: list[dict] | None = None) -> dict:
    """
    Full chat pipeline:
      1. NL → SQL
      2. Execute SQL
      3. SQL results → grounded answer

    Returns dict with:
      - answer: str
      - sql: str | None
      - results: list[dict]
      - highlighted_ids: list[str]  — node IDs to highlight in graph
      - error: str | None
    """
    sql = None
    results = []
    error = None

    try:
        # Step 1: Generate SQL
        sql = nl_to_sql(question)

        if sql is None:
            return {
                "answer": "I could not generate a valid query for this question. "
                          "Please rephrase or ask about sales orders, deliveries, "
                          "billing documents, or journal entries.",
                "sql": None,
                "results": [],
                "highlighted_ids": [],
                "error": None,
            }

        # Step 2: Execute SQL
        results = execute_query(sql)

        # Step 3: Generate grounded answer
        answer = generate_answer(question, results)

        # Extract node IDs to highlight in the graph
        highlighted_ids = _extract_node_ids(results)

    except ValueError as e:
        # Non-SELECT queries attempted
        error = str(e)
        answer = "The generated query was invalid. Please try rephrasing your question."
    except Exception as e:
        error = str(e)
        answer = f"An error occurred while processing your query: {error}"

    return {
        "answer": answer,
        "sql": sql,
        "results": results[:20],       # Cap results for payload size
        "highlighted_ids": highlighted_ids if sql else [],
        "error": error,
    }


def _extract_node_ids(results: list[dict]) -> list[str]:
    """
    Extract known graph node IDs from SQL results to highlight in the graph.
    Looks for values matching our node ID patterns.
    """
    import re
    node_ids = set()
    patterns = [
        r"SO-\d+",          # Sales orders
        r"DEL-\d+",         # Deliveries
        r"BILL-\d+",        # Billing documents
        r"JE-\d+",          # Journal entries
    ]
    combined = re.compile("|".join(patterns))

    for row in results:
        for v in row.values():
            if isinstance(v, str):
                matches = combined.findall(v)
                node_ids.update(matches)

    return list(node_ids)
