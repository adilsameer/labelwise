"""Turns one label from labels.jsonl into one output record (schema.json)."""
from labelwise.claims import find_claims
from labelwise.evidence import build_evidence
from labelwise.lookup import identify
from labelwise.rows import build_rows, public


def process_label(label, copies=None):
    """copies: optional dict that collects the evidence copies to store {copy_path: entry}."""
    rows = build_rows(label)
    for row in rows:
        identify(row)
    claims, candidates, for_a_person = find_claims(label, rows)
    evidence, found = build_evidence(rows)
    if copies is not None:
        copies.update(found)
    return {
        "label_id": label["label_id"],
        "rows": [public(r) for r in rows],
        "claims": claims,
        "candidates": candidates,
        "for_a_person": for_a_person,
        "evidence": evidence,
    }
