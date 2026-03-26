"""
guardrails.py — Pre-LLM guardrail to detect off-topic queries.
Runs a fast keyword check before spending an API call.
"""

# Keywords that are relevant to the Order-to-Cash domain.
# If the query matches NONE of these, it is rejected.
O2C_KEYWORDS = [
    # Document types
    "billing", "bill", "invoice", "order", "sales order", "delivery",
    "journal", "journal entry", "accounting document",
    # Business entities
    "customer", "material", "product", "vendor",
    "company code", "profit center", "cost center",
    # Statuses / actions
    "status", "delivered", "posted", "completed", "blocked", "transit",
    "flow", "trace", "find", "show", "list", "count", "highest", "broken",
    "amount", "currency", "fiscal", "gl account",
    # IDs commonly used in queries
    "so-", "del-", "bill-", "je-", "91150", "94006",
    "cust-", "mat-",
]

REJECTION_MESSAGE = (
    "This system only answers questions related to the provided dataset "
    "(Order-to-Cash: sales orders, deliveries, billing documents, journal entries). "
    "Please ask something related to this data."
)


def is_relevant(query: str) -> bool:
    """
    Return True if the query seems related to the O2C dataset.
    Simple keyword matching — fast and zero-cost.
    """
    lowered = query.lower()
    return any(kw in lowered for kw in O2C_KEYWORDS)
