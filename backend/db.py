"""
db.py — SQLite database initialization, seeding, and query execution.
Handles all database interactions for the Dodge AI backend.
"""

import sqlite3
import json
import os
import csv

DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")
CSV_PATH = os.path.join(os.path.dirname(__file__), "seed_data.csv")


def get_connection():
    """Return a SQLite connection with row factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all tables and seed data if DB doesn't exist yet."""
    conn = get_connection()
    cur = conn.cursor()

    # --- Relational tables (used by LLM for SQL queries) ---
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS sales_orders (
            id TEXT PRIMARY KEY,
            customer TEXT,
            material TEXT,
            quantity REAL,
            amount REAL,
            status TEXT
        );

        CREATE TABLE IF NOT EXISTS deliveries (
            id TEXT PRIMARY KEY,
            sales_order_id TEXT,
            delivery_date TEXT,
            status TEXT,
            FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id)
        );

        CREATE TABLE IF NOT EXISTS billing_documents (
            id TEXT PRIMARY KEY,
            delivery_id TEXT,
            amount REAL,
            billing_date TEXT,
            status TEXT,
            FOREIGN KEY (delivery_id) REFERENCES deliveries(id)
        );

        CREATE TABLE IF NOT EXISTS journal_entries (
            id TEXT PRIMARY KEY,
            billing_doc_id TEXT,
            gl_account TEXT,
            amount REAL,
            posting_date TEXT,
            doc_type TEXT,
            company_code TEXT,
            fiscal_year TEXT,
            reference_document TEXT,
            cost_center TEXT,
            profit_center TEXT,
            transaction_currency TEXT,
            amount_in_transaction_currency REAL,
            company_code_currency TEXT,
            amount_in_company_code_currency REAL,
            accounting_document_item INTEGER,
            accounting_document_type TEXT,
            FOREIGN KEY (billing_doc_id) REFERENCES billing_documents(id)
        );

        -- Graph tables (used for graph visualization)
        CREATE TABLE IF NOT EXISTS graph_nodes (
            id TEXT PRIMARY KEY,
            type TEXT,
            label TEXT,
            properties TEXT  -- JSON blob
        );

        CREATE TABLE IF NOT EXISTS graph_edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            target TEXT,
            relationship TEXT
        );
    """)
    conn.commit()

    # Only seed if tables are empty
    existing = cur.execute("SELECT COUNT(*) FROM sales_orders").fetchone()[0]
    if existing == 0:
        _seed_from_csv(conn, cur)

    conn.close()


def _seed_from_csv(conn, cur):
    """Parse seed_data.csv and populate all tables + graph tables."""
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Helper: strip empty strings to None
    def val(row, key):
        v = row.get(key, "").strip()
        return v if v else None

    for row in rows:
        etype = val(row, "entity_type")

        if etype == "SalesOrder":
            cur.execute(
                "INSERT OR IGNORE INTO sales_orders VALUES (?,?,?,?,?,?)",
                (val(row,"id"), val(row,"customer"), val(row,"material"),
                 val(row,"quantity"), val(row,"amount"), val(row,"status"))
            )
            props = {"customer": val(row,"customer"), "material": val(row,"material"),
                     "quantity": val(row,"quantity"), "amount": val(row,"amount"),
                     "status": val(row,"status")}
            cur.execute(
                "INSERT OR IGNORE INTO graph_nodes VALUES (?,?,?,?)",
                (val(row,"id"), "SalesOrder", val(row,"id"), json.dumps(props))
            )

        elif etype == "Delivery":
            cur.execute(
                "INSERT OR IGNORE INTO deliveries VALUES (?,?,?,?)",
                (val(row,"id"), val(row,"sales_order_id"),
                 val(row,"delivery_date"), val(row,"delivery_status"))
            )
            props = {"sales_order_id": val(row,"sales_order_id"),
                     "delivery_date": val(row,"delivery_date"),
                     "status": val(row,"delivery_status")}
            cur.execute(
                "INSERT OR IGNORE INTO graph_nodes VALUES (?,?,?,?)",
                (val(row,"id"), "Delivery", val(row,"id"), json.dumps(props))
            )
            # Edge: SalesOrder → Delivery
            cur.execute(
                "INSERT INTO graph_edges (source, target, relationship) VALUES (?,?,?)",
                (val(row,"sales_order_id"), val(row,"id"), "HAS_DELIVERY")
            )

        elif etype == "BillingDocument":
            cur.execute(
                "INSERT OR IGNORE INTO billing_documents VALUES (?,?,?,?,?)",
                (val(row,"id"), val(row,"delivery_id"), val(row,"billing_amount"),
                 val(row,"billing_date"), val(row,"billing_status"))
            )
            props = {"delivery_id": val(row,"delivery_id"),
                     "amount": val(row,"billing_amount"),
                     "billing_date": val(row,"billing_date"),
                     "status": val(row,"billing_status")}
            cur.execute(
                "INSERT OR IGNORE INTO graph_nodes VALUES (?,?,?,?)",
                (val(row,"id"), "BillingDocument", val(row,"id"), json.dumps(props))
            )
            # Edge: Delivery → BillingDocument
            cur.execute(
                "INSERT INTO graph_edges (source, target, relationship) VALUES (?,?,?)",
                (val(row,"delivery_id"), val(row,"id"), "HAS_BILLING")
            )

        elif etype == "JournalEntry":
            cur.execute(
                """INSERT OR IGNORE INTO journal_entries VALUES
                   (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (val(row,"id"), val(row,"billing_doc_id"), val(row,"gl_account"),
                 val(row,"posting_amount"), val(row,"posting_date"), val(row,"doc_type"),
                 val(row,"company_code"), val(row,"fiscal_year"),
                 val(row,"reference_document"), val(row,"cost_center"),
                 val(row,"profit_center"), val(row,"transaction_currency"),
                 val(row,"amount_in_transaction_currency"),
                 val(row,"company_code_currency"),
                 val(row,"amount_in_company_code_currency"),
                 val(row,"accounting_document_item"),
                 val(row,"accounting_document_type"))
            )
            props = {"billing_doc_id": val(row,"billing_doc_id"),
                     "gl_account": val(row,"gl_account"),
                     "amount": val(row,"posting_amount"),
                     "posting_date": val(row,"posting_date"),
                     "doc_type": val(row,"doc_type"),
                     "company_code": val(row,"company_code"),
                     "fiscal_year": val(row,"fiscal_year"),
                     "reference_document": val(row,"reference_document"),
                     "profit_center": val(row,"profit_center"),
                     "transaction_currency": val(row,"transaction_currency"),
                     "amount_in_transaction_currency": val(row,"amount_in_transaction_currency"),
                     "company_code_currency": val(row,"company_code_currency"),
                     "amount_in_company_code_currency": val(row,"amount_in_company_code_currency"),
                     "accounting_document_item": val(row,"accounting_document_item"),
                     "accounting_document_type": val(row,"accounting_document_type")}
            cur.execute(
                "INSERT OR IGNORE INTO graph_nodes VALUES (?,?,?,?)",
                (val(row,"id"), "JournalEntry", val(row,"id"), json.dumps(props))
            )
            # Edge: BillingDocument → JournalEntry
            cur.execute(
                "INSERT INTO graph_edges (source, target, relationship) VALUES (?,?,?)",
                (val(row,"billing_doc_id"), val(row,"id"), "HAS_JOURNAL")
            )

    conn.commit()
    print(f"✅ Seeded database from {CSV_PATH}")


def execute_query(sql: str) -> list[dict]:
    """
    Execute a SQL SELECT query and return results as list of dicts.
    Raises ValueError for non-SELECT queries (safety guard).
    """
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed.")

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


# Schema description injected into LLM prompts
DB_SCHEMA = """
Tables in the SQLite database:

1. sales_orders
   - id TEXT (e.g. SO-1001)
   - customer TEXT (e.g. CUST-001)
   - material TEXT (e.g. MAT-PUMP-A)
   - quantity REAL
   - amount REAL
   - status TEXT ('Completed', 'InProgress', 'Blocked')

2. deliveries
   - id TEXT (e.g. DEL-2001)
   - sales_order_id TEXT → references sales_orders.id
   - delivery_date TEXT (YYYY-MM-DD)
   - status TEXT ('Delivered', 'InTransit')

3. billing_documents
   - id TEXT (e.g. BILL-91150187)
   - delivery_id TEXT → references deliveries.id
   - amount REAL
   - billing_date TEXT (YYYY-MM-DD)
   - status TEXT ('Posted', 'Cancelled')

4. journal_entries
   - id TEXT (e.g. JE-9400635958)
   - billing_doc_id TEXT → references billing_documents.id
   - gl_account TEXT
   - amount REAL
   - posting_date TEXT (YYYY-MM-DD)
   - doc_type TEXT
   - company_code TEXT
   - fiscal_year TEXT
   - reference_document TEXT
   - cost_center TEXT
   - profit_center TEXT
   - transaction_currency TEXT
   - amount_in_transaction_currency REAL
   - company_code_currency TEXT
   - amount_in_company_code_currency REAL
   - accounting_document_item INTEGER
   - accounting_document_type TEXT

Relationships:
  sales_orders → deliveries (via deliveries.sales_order_id)
  deliveries → billing_documents (via billing_documents.delivery_id)
  billing_documents → journal_entries (via journal_entries.billing_doc_id)
"""
