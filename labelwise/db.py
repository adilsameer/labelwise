"""Part D: load the output folder into one SQLite file.

python -m labelwise.db [output]   (run.py calls this at the end)

Why this design:
1. A substance is one row in `identities` and its evidence is one row in `evidence`, shared by every
   label that uses it, so a hazard is stored once and found from any label with one join.
2. `rows`, `claims`, `candidates` and `for_a_person` keep the label's own words (verbatim, quote) next
   to the parsed fields, and `labels.raw_text` is kept, so every quote can be checked in SQL.
3. Review reasons are split into `reason_code` + `reason`, so the review queue is a GROUP BY.
"""
import json
import sqlite3
import sys
from pathlib import Path

SCHEMA = """
CREATE TABLE labels (
    label_id    TEXT PRIMARY KEY,
    source      TEXT NOT NULL,            -- dsld | retailer
    source_url  TEXT,
    title       TEXT,
    brand       TEXT,
    serving     TEXT,
    raw_text    TEXT NOT NULL
);

CREATE TABLE identities (
    system      TEXT NOT NULL,            -- pubchem_cid | unii | ncbi_taxid
    id          TEXT NOT NULL,
    lookup_url  TEXT NOT NULL,
    PRIMARY KEY (system, id)
);

CREATE TABLE evidence (
    system      TEXT NOT NULL,
    id          TEXT NOT NULL,
    source      TEXT NOT NULL,            -- pubchem_ghs
    status      TEXT NOT NULL CHECK (status IN ('record', 'no_record')),  -- no_record never means safe
    summary     TEXT,
    date        TEXT NOT NULL,
    url         TEXT NOT NULL,
    copy_path   TEXT NOT NULL,
    PRIMARY KEY (system, id, source),
    FOREIGN KEY (system, id) REFERENCES identities (system, id)
);

CREATE TABLE rows (
    label_id         TEXT NOT NULL REFERENCES labels (label_id),
    row_id           TEXT NOT NULL,
    position         INTEGER NOT NULL,    -- label order
    verbatim         TEXT NOT NULL,
    parent           TEXT,
    form             TEXT,
    source           TEXT,
    strain           TEXT,
    standardization  TEXT,
    role             TEXT NOT NULL CHECK (role IN ('ingredient', 'blend_header', 'blend_member', 'excipient')),
    group_row_id     TEXT,                -- the blend header this row is in
    amount_value     REAL,
    amount_unit      TEXT,
    amount_scope     TEXT,
    blend_contents   TEXT,
    identity_system  TEXT,
    identity_id      TEXT,
    status           TEXT NOT NULL CHECK (status IN ('identified', 'review')),
    reason_code      TEXT,
    reason           TEXT,
    PRIMARY KEY (label_id, row_id),
    FOREIGN KEY (identity_system, identity_id) REFERENCES identities (system, id)
);

CREATE TABLE claims (
    label_id     TEXT NOT NULL REFERENCES labels (label_id),
    claim_id     TEXT NOT NULL,           -- C01..C40 from claims.md
    claim        TEXT NOT NULL,
    quote        TEXT NOT NULL,
    where_field  TEXT NOT NULL,
    PRIMARY KEY (label_id, claim_id)
);

CREATE TABLE candidates (
    label_id  TEXT NOT NULL REFERENCES labels (label_id),
    n         INTEGER NOT NULL,
    phrase    TEXT NOT NULL,
    quote     TEXT NOT NULL,
    PRIMARY KEY (label_id, n)
);

CREATE TABLE for_a_person (
    label_id  TEXT NOT NULL REFERENCES labels (label_id),
    n         INTEGER NOT NULL,
    kind      TEXT NOT NULL CHECK (kind IN ('conflict', 'exception', 'unclear')),
    note      TEXT NOT NULL,
    quote     TEXT NOT NULL,
    PRIMARY KEY (label_id, n)
);

CREATE INDEX rows_identity ON rows (identity_system, identity_id);
CREATE INDEX rows_reason ON rows (reason_code);
"""


def build(out_dir, labels_path):
    out_dir = Path(out_dir)
    db_path = out_dir / "labelwise.sqlite"
    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript(SCHEMA)

    labels = [json.loads(line) for line in open(labels_path, encoding="utf-8") if line.strip()]
    for lab in labels:
        con.execute("INSERT INTO labels VALUES (?,?,?,?,?,?,?)",
                    (lab["label_id"], lab["source"], lab.get("source_url"), lab.get("title"), lab.get("brand"),
                     lab.get("serving"), lab["raw_text"]))

    for lab in labels:
        data = json.loads((out_dir / (lab["label_id"].replace(":", "_") + ".json")).read_text())
        lid = data["label_id"]
        by_row = {r["row_id"]: r for r in data["rows"]}
        for pos, r in enumerate(data["rows"], 1):
            ident = r["identity"]
            if ident:
                con.execute("INSERT OR IGNORE INTO identities VALUES (?,?,?)",
                            (ident["system"], ident["id"], ident["lookup_url"]))
            code = r["reason"].split(":")[0] if r["reason"] else None
            con.execute("INSERT INTO rows VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (lid, r["row_id"], pos, r["verbatim"], r["parent"], r["form"], r["source"], r["strain"],
                         r["standardization"], r["role"], r["group"], r["amount"]["value"], r["amount"]["unit"],
                         r["amount"]["scope"], r["blend_contents"], ident and ident["system"], ident and ident["id"],
                         r["status"], code, r["reason"]))
        for e in data["evidence"]:
            ident = by_row[e["row_id"]]["identity"]
            con.execute("INSERT OR IGNORE INTO evidence VALUES (?,?,?,?,?,?,?,?)",
                        (ident["system"], ident["id"], e["source"], e["status"], e["summary"], e["date"],
                         e["url"], e["copy_path"]))
        for c in data["claims"]:
            con.execute("INSERT INTO claims VALUES (?,?,?,?,?)", (lid, c["claim_id"], c["claim"], c["quote"], c["where"]))
        for n, c in enumerate(data["candidates"], 1):
            con.execute("INSERT INTO candidates VALUES (?,?,?,?)", (lid, n, c["phrase"], c["quote"]))
        for n, p in enumerate(data["for_a_person"], 1):
            con.execute("INSERT INTO for_a_person VALUES (?,?,?,?,?)", (lid, n, p["kind"], p["note"], p["quote"]))
    con.commit()
    con.execute("VACUUM")
    con.close()
    return db_path


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    print(build(sys.argv[1] if len(sys.argv) > 1 else root / "output", root / "labels.jsonl"))
