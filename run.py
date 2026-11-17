"""Run the whole pipeline: python run.py [--labels labels.jsonl] [--out output] [--offline]"""
import argparse
import hashlib
import json
import shutil
import subprocess
import time
from collections import Counter
from pathlib import Path

from labelwise import db, fetch
from labelwise.pipeline import process_label

ROOT = Path(__file__).resolve().parent


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def code_version():
    try:
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                             text=True, check=True).stdout.strip()
        if sha:
            return sha
    except (OSError, subprocess.CalledProcessError):
        pass
    h = hashlib.sha256()
    for p in sorted([ROOT / "run.py", *(ROOT / "labelwise").glob("*.py")]):
        h.update(p.read_bytes())
    return "code-sha256:" + h.hexdigest()[:16]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", default=str(ROOT / "labels.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "output"))
    ap.add_argument("--offline", action="store_true", help="use only the cache; never call the network")
    args = ap.parse_args()

    fetch.offline = args.offline
    out = Path(args.out)
    start = time.monotonic()

    labels = [json.loads(line) for line in open(args.labels, encoding="utf-8") if line.strip()]
    results, copies = [], {}
    for label in labels:
        result = process_label(label, copies)
        write_json(out / (label["label_id"].replace(":", "_") + ".json"), result)
        results.append(result)

    shutil.rmtree(out / "evidence", ignore_errors=True)  # drop copies an older run left behind
    for path, entry in sorted(copies.items()):
        write_json(out / path, entry)

    rows = [r for res in results for r in res["rows"]]
    review_rows = [r for r in rows if r["status"] == "review"]
    write_json(out / "review_queue.json", {
        "review": dict(sorted(Counter(r["reason"].split(":")[0] for r in review_rows).items())),
        "candidates": sum(len(res["candidates"]) for res in results),
        "for_a_person": sum(len(res["for_a_person"]) for res in results),
        "no_record": sum(1 for res in results for e in res["evidence"] if e["status"] == "no_record"),
    })
    write_json(out / "run_report.json", {
        "labels": len(results),
        "rows": len(rows),
        "identified": len(rows) - len(review_rows),
        "review": len(review_rows),
        "seconds": round(time.monotonic() - start, 2),
        "version": code_version(),
    })
    db.build(out, args.labels)
    print(f"{len(results)} labels, {len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()
