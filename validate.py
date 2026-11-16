"""Check an output folder against schema.json and the quote rule.

python validate.py [--out output]
"""
import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "output"))
    ap.add_argument("--labels", default=str(ROOT / "labels.jsonl"))
    args = ap.parse_args()
    out = Path(args.out)

    schema = json.loads((ROOT / "schema.json").read_text())
    defs = schema["$defs"]
    label_v = Draft202012Validator(schema)
    queue_v = Draft202012Validator({**defs["review_queue"], "$defs": defs})
    report_v = Draft202012Validator({**defs["run_report"], "$defs": defs})

    raw = {}
    for line in open(args.labels, encoding="utf-8"):
        if line.strip():
            label = json.loads(line)
            raw[label["label_id"]] = label["raw_text"]

    errors = []
    for label_id, text in raw.items():
        path = out / (label_id.replace(":", "_") + ".json")
        if not path.exists():
            errors.append(f"{path.name}: missing")
            continue
        data = json.loads(path.read_text())
        errors += [f"{path.name}: {e.json_path}: {e.message}" for e in label_v.iter_errors(data)]
        for part in ("claims", "candidates", "for_a_person"):
            for i, item in enumerate(data.get(part, [])):
                if item["quote"] not in text:
                    errors.append(f"{path.name}: {part}[{i}] quote not in raw_text: {item['quote']!r}")
        for ev in data.get("evidence", []):
            if not (out / ev["copy_path"]).exists():
                errors.append(f"{path.name}: evidence copy missing: {ev['copy_path']}")

    for name, v in (("review_queue.json", queue_v), ("run_report.json", report_v)):
        data = json.loads((out / name).read_text())
        errors += [f"{name}: {e.json_path}: {e.message}" for e in v.iter_errors(data)]

    for e in errors:
        print(e)
    print(f"{len(raw)} labels checked, {len(errors)} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
