"""
graph.py — Build graph JSON from the SQLite database.
Returns the {nodes, links} format consumed by react-force-graph.
"""

import json
from db import get_connection

# Color per node type (used as metadata for frontend coloring)
NODE_COLORS = {
    "SalesOrder":      "#4f9cf9",   # blue
    "Delivery":        "#f97b4f",   # orange
    "BillingDocument": "#a78bfa",   # purple
    "JournalEntry":    "#34d399",   # green
}


def get_graph_data() -> dict:
    """
    Fetch all nodes and edges from the DB and return them as
    a dict with 'nodes' and 'links' keys (react-force-graph format).
    """
    conn = get_connection()
    cur = conn.cursor()

    # Fetch nodes
    rows = cur.execute("SELECT id, type, label, properties FROM graph_nodes").fetchall()
    nodes = []
    for row in rows:
        props = json.loads(row["properties"]) if row["properties"] else {}
        nodes.append({
            "id":    row["id"],
            "type":  row["type"],
            "label": row["label"],
            "color": NODE_COLORS.get(row["type"], "#999999"),
            **props,          # Flatten all properties into the node object
        })

    # Fetch edges
    rows = cur.execute(
        "SELECT source, target, relationship FROM graph_edges"
    ).fetchall()
    links = [
        {"source": row["source"], "target": row["target"], "label": row["relationship"]}
        for row in rows
    ]

    conn.close()
    return {"nodes": nodes, "links": links}
