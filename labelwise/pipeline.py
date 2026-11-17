"""Turns one label from labels.jsonl into one output record (schema.json)."""
from labelwise.claims import find_claims
from labelwise.lookup import identify
from labelwise.rows import build_rows, public


def process_label(label):
    rows = build_rows(label)
    for row in rows:
        identify(row)
    claims, candidates, for_a_person = find_claims(label, rows)
    return {
        "label_id": label["label_id"],
        "rows": [public(r) for r in rows],
        "claims": claims,
        "candidates": candidates,
        "for_a_person": for_a_person,
        "evidence": [],
    }
