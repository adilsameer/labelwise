"""Turns one label from labels.jsonl into one output record (schema.json)."""
from labelwise.rows import build_rows, public


def process_label(label):
    rows = build_rows(label)
    for row in rows:
        if row["reason"] is None:
            row["reason"] = "pending_lookup"
    return {
        "label_id": label["label_id"],
        "rows": [public(r) for r in rows],
        "claims": [],
        "candidates": [],
        "for_a_person": [],
        "evidence": [],
    }
