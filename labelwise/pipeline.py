"""Turns one label from labels.jsonl into one output record (schema.json)."""


def process_label(label):
    return {
        "label_id": label["label_id"],
        "rows": [],
        "claims": [],
        "candidates": [],
        "for_a_person": [],
        "evidence": [],
    }
