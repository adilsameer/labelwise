"""Check every identified id against the name the source gives for it.

python audit_ids.py [--out output]   -> prints rows whose name and source name share no word.
Writes audit_ids.tsv with every identified row for a hand check.
"""
import argparse
import csv
import glob
import json
import re
from pathlib import Path

from labelwise.fetch import fetch_json
from labelwise.lookup import ncbi_names

ROOT = Path(__file__).resolve().parent


def source_names(ident):
    system, id_ = ident["system"], ident["id"]
    if system == "pubchem_cid":
        _, j = fetch_json(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{id_}/synonyms/JSON")
        return j["InformationList"]["Information"][0].get("Synonym", [])[:40] if j else []
    if system == "unii":
        _, j = fetch_json(f"https://gsrs.ncats.nih.gov/api/v1/substances({id_})/names")
        return [n["name"] for n in j][:40] if isinstance(j, list) else []
    return [ncbi_names([id_]).get(id_, ("",))[0]]


def words(text):
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(w) > 2}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "output"))
    args = ap.parse_args()

    out_rows, flagged = [], 0
    for path in sorted(glob.glob(f"{args.out}/dsld_*.json") + glob.glob(f"{args.out}/retailer_*.json")):
        data = json.loads(Path(path).read_text())
        for r in data["rows"]:
            if r["status"] != "identified":
                continue
            names = source_names(r["identity"])
            label_words = words(r["form"]) | words(r["parent"]) | words(r["verbatim"])
            ok = any(label_words & words(n) for n in names)
            flagged += not ok
            out_rows.append([data["label_id"], r["row_id"], r["verbatim"], r["parent"], r["form"],
                             r["identity"]["system"], r["identity"]["id"], names[0] if names else "", "" if ok else "CHECK"])
            if not ok:
                print(f"CHECK {data['label_id']} {r['row_id']}: {r['verbatim']!r} -> {r['identity']['system']} "
                      f"{r['identity']['id']} {names[:3]}")
    with open(ROOT / "audit_ids.tsv", "w", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["label_id", "row_id", "verbatim", "parent", "form", "system", "id", "source_name", "flag"])
        w.writerows(out_rows)
    print(f"{len(out_rows)} identified rows, {flagged} with no shared word -> audit_ids.tsv")


if __name__ == "__main__":
    main()
