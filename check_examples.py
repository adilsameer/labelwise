"""Compare the program's output on examples/*/label.json with expected.json.

python check_examples.py [--part rows|claims|evidence|all]
"""
import argparse
import json
from pathlib import Path

from labelwise import fetch
from labelwise.pipeline import process_label

ROOT = Path(__file__).resolve().parent
ROW_FIELDS = ["verbatim", "parent", "form", "source", "strain", "standardization", "role", "group",
              "amount", "blend_contents", "identity", "status", "reason"]


def compare_rows(got, want):
    diffs = []
    got_by_id = {r["row_id"]: r for r in got}
    if [r["row_id"] for r in got] != [r["row_id"] for r in want]:
        diffs.append(f"row ids: got {[r['row_id'] for r in got]} want {[r['row_id'] for r in want]}")
    for w in want:
        g = got_by_id.get(w["row_id"])
        if not g:
            continue
        for f in ROW_FIELDS:
            gv, wv = g[f], w[f]
            if f == "reason":  # compare the code only; the detail text is free
                gv, wv = (gv or "").split(":")[0], (wv or "").split(":")[0]
            if gv != wv:
                diffs.append(f"{w['row_id']}.{f}: got {gv!r} want {wv!r}")
    return diffs


def compare_list(got, want, key):
    g = sorted(json.dumps({k: x[k] for k in key}, sort_keys=True) for x in got)
    w = sorted(json.dumps({k: x[k] for k in key}, sort_keys=True) for x in want)
    return [f"missing {x}" for x in w if x not in g] + [f"extra {x}" for x in g if x not in w]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="all", choices=["rows", "claims", "evidence", "all"])
    ap.add_argument("--online", action="store_true")
    args = ap.parse_args()
    fetch.offline = not args.online

    total = 0
    for ex in sorted((ROOT / "examples").iterdir()):
        if not (ex / "label.json").exists():
            continue
        got = process_label(json.loads((ex / "label.json").read_text()))
        want = json.loads((ex / "expected.json").read_text())
        diffs = []
        if args.part in ("rows", "all"):
            diffs += compare_rows(got["rows"], want["rows"])
        if args.part in ("claims", "all"):
            diffs += compare_list(got["claims"], want["claims"], ["claim_id", "quote", "where"])
        if args.part in ("evidence", "all"):
            diffs += compare_list(got["evidence"], want["evidence"], ["row_id", "source", "status", "url"])
        print(f"{ex.name}: {len(diffs)} differences")
        for d in diffs:
            print("   ", d)
        total += len(diffs)
    print(f"total differences: {total}")


if __name__ == "__main__":
    main()
