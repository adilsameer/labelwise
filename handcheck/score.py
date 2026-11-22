"""Turn hand-check marks into the accuracy table.

python handcheck/score.py [marks.json]   (default: handcheck/marks.json; falls back to handcheck/premarks/)
Writes handcheck/accuracy.md.
"""
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "handcheck"


def load_marks(path):
    """(marks, origin, output folder the marks judge)."""
    if path and Path(path).exists():
        return json.loads(Path(path).read_text()), Path(path).name, ROOT / "output"
    files = sorted(glob.glob(str(HERE / "premarks" / "*.json")))
    return ([json.loads(Path(f).read_text()) for f in files],
            "premarks/ (AI pre-check of the output before fixes, in premarks_base/)", HERE / "premarks_base")


def pct(ok, total):
    return f"{ok}/{total} = {100 * ok / total:.1f}%" if total else "n/a"


def main():
    marks, origin, out_dir = load_marks(sys.argv[1] if len(sys.argv) > 1 else HERE / "marks.json")
    unmarked = sum(1 for m in marks for p in ("rows", "claims", "candidates", "evidence") for x in m.get(p, [])
                   if None in (x.get("mark", "ok"), x.get("parse", "ok"), x.get("identity", "ok")))
    if unmarked:
        sys.exit(f"{unmarked} items are not marked yet; finish them in review.html first")
    t = {k: [0, 0] for k in ("parse", "id_identified", "id_review", "claims", "candidates", "evidence")}
    missed_claims = missed_rows = 0
    wrong = []
    for m in marks:
        out = json.loads((out_dir / (m["label_id"].replace(":", "_") + ".json")).read_text())
        status = {r["row_id"]: r["status"] for r in out["rows"]}
        for r in m["rows"]:
            t["parse"][1] += 1
            t["parse"][0] += r["parse"] == "ok"
            key = "id_identified" if status.get(r["row_id"]) == "identified" else "id_review"
            t[key][1] += 1
            t[key][0] += r["identity"] == "ok"
            for part in ("parse", "identity"):
                if r[part] == "wrong":
                    wrong.append(f"{m['label_id']} {r['row_id']} {part}: {r.get('note', '')}")
        missed_rows += len(m.get("missed_rows", []))
        for c in m["claims"]:
            t["claims"][1] += 1
            t["claims"][0] += c["mark"] == "ok"
            if c["mark"] == "wrong":
                wrong.append(f"{m['label_id']} {c['claim_id']} claim: {c.get('note', '')}")
        missed_claims += len(m.get("missed_claims", []))
        wrong += [f"{m['label_id']} missed {c['claim_id']}: {c.get('note', '')}" for c in m.get("missed_claims", [])]
        for part in ("candidates", "evidence"):
            for x in m.get(part, []):
                t[part][1] += 1
                t[part][0] += x["mark"] == "ok"
                if x["mark"] == "wrong":
                    wrong.append(f"{m['label_id']} {part} {x.get('row_id', x.get('n'))}: {x.get('note', '')}")

    claims_ok = t["claims"][0]
    lines = [
        f"# Hand-check accuracy ({len(marks)} labels, marks from {origin})",
        "",
        "| Area | Measure | Result |",
        "|---|---|---|",
        f"| Rows | Row fields parsed right | {pct(t['parse'][0], t['parse'][1] + missed_rows)} (missed rows count as wrong: {missed_rows}) |",
        f"| Ids | Identified rows with the right id | {pct(*t['id_identified'])} |",
        f"| Ids | Review rows where review was right | {pct(*t['id_review'])} |",
        f"| Claims | Claims precision (reported claims that are right) | {pct(claims_ok, t['claims'][1])} |",
        f"| Claims | Claims recall (right claims of all claims on the label) | {pct(claims_ok, claims_ok + missed_claims)} |",
        f"| Claims | Candidates that are claim-like and not on the list | {pct(*t['candidates'])} |",
        f"| Evidence | Evidence items right (url, status, summary) | {pct(*t['evidence'])} |",
        "",
        "## Every item marked wrong",
        "",
        *[f"- {w}" for w in wrong],
        "",
    ]
    target = "accuracy.md" if out_dir == ROOT / "output" else "accuracy_precheck.md"
    (HERE / target).write_text("\n".join(lines))
    print("\n".join(lines[:12]))
    print(f"... {len(wrong)} wrong items listed in handcheck/{target}")


if __name__ == "__main__":
    main()
