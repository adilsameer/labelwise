# LabelWise: supplement labels to rows, claims and evidence

One program reads the 100 supplement labels in `labels.jsonl` and writes one JSON file per label (`schema.json`),
plus `review_queue.json`, `run_report.json` and `labelwise.sqlite`.

Three rules hold everywhere:

1. Every id comes from a lookup in a public source. No id is typed by hand or taken from an AI model.
2. No AI model runs inside the program.
3. `no_record` never means safe. It only means that the source has no record.

## How to run

Python 3 (tested on 3.12).

```sh
python3 -m pip install -r requirements.txt   # jsonschema (checks only), certifi (TLS on macOS)

python3 run.py --offline   # from the committed cache: about 1 second, the same output every time
python3 run.py             # live: fetches any URL that is not in cache/ yet, then stores it
```

Output goes to `output/`: `<label_id>.json` (`:` becomes `_`), `evidence/pubchem_ghs/<id>.json` (the stored
copies), `review_queue.json`, `run_report.json`, `labelwise.sqlite`.

Checks:

```sh
python3 validate.py          # every file against schema.json, every quote is a substring of raw_text, copies exist
python3 check_examples.py    # our output for examples/ against expected.json
python3 -m unittest          # 15 rule tests on real labels, offline
python3 audit_ids.py         # ids whose PubChem/GSRS name shares no word with the label name
python3 handcheck/score.py handcheck/marks.json   # accuracy on the 20 hand-checked labels
```

## How it works

```
labels.jsonl
  -> rows.py      split each label into rows; parse parent, form, source, strain, standardization, role, amount
  -> lookup.py    one public id per row, or review + reason
  -> claims.py    claims C01-C40, candidates, for_a_person
  -> evidence.py  PubChem GHS record for each identified id, copy stored with date and link
  -> run.py       label files, review_queue.json, run_report.json; db.py loads it all into SQLite
```

**Same output on every run.** Every web call goes through `labelwise/fetch.py`. The answer is stored once in
`cache/<sha1(url)>.json` with the date it was fetched, and every later run reads it from there. The cache is
committed. With `--offline`, a URL missing from the cache is an error, never a live call. Server errors
(5xx, 429) are retried with backoff and never stored. 404 ("no such name") is a real answer and is stored.

**Ids.** Every id comes from a lookup answer (rule 1). `labelwise/rules.py` holds names and spellings only.
A row is `identified` only when one source gives exactly one match that passes a check. Otherwise it is
`review`, with a reason code. In order of strength:

1. The PubChem title of the only CID for the name is the name itself. Skipped for plant and food rows,
   because "Amaranth" is also the title of a dye.
2. GSRS (FDA) has a record with this exact name. Its UNII is mapped to a CID through PubChem's own UNII
   cross-reference, and the CID whose title matches wins. If no single CID fits, the id is the UNII.
3. The name is one of the first 10 PubChem synonyms of the only CID. Deeper synonyms are rejected:
   "kelp" is a synonym of the drug astemizole.

Rows with a chemical form ("Zinc (as zinc oxide)") get the id of the form. A vitamin or mineral with no form
("Vitamin C 500 mg") goes to review as `form_not_given`, with the nearest id. Botanicals go from the most specific
GSRS name to the least ("Curcuma longa root extract", then "Curcuma longa root", then "Curcuma longa"). NCBI checks
that the GSRS record is made from the same organism. Microbes get an NCBI Taxonomy id, at strain level when NCBI has
the strain.

**Claims.** The label text is cut into statements (lines, sentences, bullets) and matched against the
tables at the top of `labelwise/claims.py`. Ingredient lists are skipped: "gluten" there is an ingredient, not a
claim. Every quote is cut from `raw_text`, so it is always an exact substring. The program finds four kinds of
conflict for `for_a_person`:

- vegan or vegetarian next to an animal row
- "X free" next to a row or a "Contains" statement with X
- sugar free next to a sugars row above 0
- "free of X except Y"

Unclear wording also goes there ("nuts", "Hala"). Claim-like text that is not in `claims.md` becomes a candidate.

**Evidence.** One source, PubChem GHS classification, for each identified row. The full response is stored
with its URL and date. A response with no GHS section is `no_record`. **`no_record` never means safe** (rule 3): it
only means PubChem has no GHS record for that id.

## Database

`output/labelwise.sqlite`, built at the end of every run from the output folder (`labelwise/db.py`).

```sql
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
```

Why this design:

1. A substance is one row in `identities` and its evidence is one row in `evidence`, shared by every label that uses it, so a hazard is stored once and found from any label with one join.
2. `rows`, `claims`, `candidates` and `for_a_person` keep the label's own words (verbatim, quote) next to the parsed fields, and `labels.raw_text` is kept, so every quote can be checked in SQL.
3. Review reasons are split into `reason_code` and `reason`, so the review queue is a `GROUP BY`.

## Results of the full run

100 labels, 1543 rows: 811 identified (516 PubChem CID, 269 UNII, 26 NCBI Taxonomy) and 732 review.
533 claims, 184 candidates, 7 for_a_person items. 811 evidence items: 461 `record`, 350 `no_record`.

## Accuracy on 20 hand-checked labels

The labels were drawn at random with a fixed seed (`handcheck/sample.py`, seed 20261117): 10 DSLD and 10 retailer.
Each row, claim, candidate and evidence item was marked right or wrong in `handcheck/review.html`, and missed
rows and missed claims were added. `handcheck/score.py` turns the marks into the table.

**TODO (Adil): paste the table from `handcheck/accuracy.md` here after marking.**

For comparison: an AI pre-check of an earlier version of the output, before the last round of fixes
(`handcheck/accuracy_precheck.md`), gave these numbers. They are not the final accuracy.

| Area | Measure | AI pre-check, earlier output |
|---|---|---|
| Rows | Row fields parsed right (missed rows count as wrong) | 68.9% |
| Ids | Identified rows with the right id | 93.0% |
| Ids | Review rows where review was right | 77.6% |
| Claims | Claims precision / recall | 98.2% / 93.3% |
| Claims | Candidates that are claim-like and not in the list | 95.1% |
| Evidence | Evidence items right | 91.9% |

## Label patterns the program cannot handle

Row patterns, from `output/review_queue.json` (1543 rows in all):

| Pattern | Rows | What the program does |
|---|---|---|
| Nutrition panel rows (calories, fat, sodium, sugars) | 174 | review `nutrition_panel` |
| No exact name in PubChem or GSRS (marketing names, house blends, typos) | 170 | review `no_match` |
| Form named, but no id for that form (extracts, concentrates, chelates) | 129 | review `form_no_id`, nearest id given |
| Vitamin or mineral with no form ("Vitamin C 60 mg") | 86 | review `form_not_given`, nearest id given |
| A class or mixture, not one substance ("natural flavors", "EPA/DHA") | 55 | review `not_one_substance` |
| Blend headers (a blend has no single id) | 51 | review `blend_header` |
| Ambiguous names ("vegetable capsule", "amaranth") | 37 | review `ambiguous_name` |
| Several forms in one row ("as zinc picolinate, citrate") | 13 | review `multiple_forms`, nearest id given |
| The name is only a minor PubChem synonym | 11 | review `weak_synonym` |
| Probiotic strain not in NCBI | 6 | review `strain_no_id` |

Evidence patterns:

| Pattern | Items | Result |
|---|---|---|
| UNII with no single PubChem CID, so no GHS record can be looked up | 269 | `no_record` |
| NCBI Taxonomy ids (microbes): PubChem GHS has no records for organisms | 26 | `no_record` |
| PubChem CID with no GHS section | 55 | `no_record` |

Label patterns:

| Pattern | Labels | Example |
|---|---|---|
| Spelling errors in the source ("lodine", "lodide") | 3 | retailer:24336 "potassium lodide" goes to `no_match` |
| Other source typos ("fermetum", "Hala", "Non GMP") | 3 | retailer:62350, retailer:26942, retailer:22659 |
| Retailer ingredient text with a missing comma: two items join into one row | 2 (5 rows) | retailer:29300 "organic high oleic sunflower oil organic cane sugar" |
| Unbalanced brackets in the ingredient text | 1 | retailer:16751: blend members leak into the next item |
| Nested blends in retailer text, where only one level is kept | not counted | retailer:64033 |
| Labels with `raw_text` only | 4 | parsed from `raw_text` with simpler rules; all 4 get rows |

Limit: an id found by pass 1 or 3 above rests on PubChem alone. No second source confirms it.

## What AI did, and how the AI's work was checked

**TODO (Adil): put this in your own words.** Draft:

- The code was written with Claude Code (an AI coding agent). It wrote the parser, the lookup chain, the claim
  tables, the evidence code, the database and the check scripts, one step at a time. At each step I chose between
  options: the id sources and their order, what goes to review, the conflict rules, the database design.
- No AI model runs in the program (rule 2), and no id comes from an AI model (rule 1): every id is in a cached
  PubChem, GSRS or NCBI answer, so each one can be traced to its stored response in `cache/`.
- How the AI's work was checked:
  - **Worked examples:** `check_examples.py` shows 0 differences on all three.
  - **Schema and quotes:** `validate.py` shows 0 errors on 100 labels.
  - **Id audit:** `audit_ids.py` lists every id whose source name shares no word with the label name. Today 3 of
    811 are listed, and all 3 are right (HPMC is hypromellose, for example). This audit found the wrong ids
    listed under "What did not work".
  - **Rule tests:** `tests/` holds one test for each bug that was fixed, run against real labels.
  - **Reruns:** an offline rerun gives byte-identical files (only the run time in `run_report.json` changes).
  - **Second AI solution:** a second AI agent solved the same problem separately, and its ids were compared with
    ours. It trusted the PubChem number stored inside GSRS records. That gave wrong ids (papain became CID 9369,
    beta-alanylhistidine), so we kept our lookup chain and took over its better rules for retailer ingredient
    lists and allergen statements.
  - **AI pre-check, then a human check:** four AI reviewers marked the 20 sample labels first. Those marks are in
    `handcheck/premarks/`, next to the exact output they judged in `handcheck/premarks_base/`. I then checked
    every item by hand. Items that changed after the pre-check were left blank for me to mark fresh.

## What did not work

- **PubChem name search first.** It matches deep synonyms: "kelp" gave the drug astemizole. Fixed by trying
  GSRS exact names first and accepting only the first 10 PubChem synonyms.
- **The PubChem number inside GSRS records.** Some are wrong (papain's record points to beta-alanylhistidine).
  We map UNII to CID through PubChem's own cross-reference and check the title.
- **Free-text GSRS search.** It returned close but different substances. Exact name search
  (`root_names_name:"^NAME$"`) fixed that.
- **GSRS answers for food rows.** "Amaranth" (a grain) was identified as the dye amaranth. Food and plant rows
  now reject GSRS chemical records.
- **Removing repeated Supplement Facts names from retailer ingredient text.** It also cut real ingredients:
  "magnesium sulfate" became "sulfate", and "thiamine hydrochloride" became "e hydrochloride". It now removes a
  name only when it is not followed by more of the same ingredient.
- **A strain regex on normalised text.** It broke the probiotic example. Replaced by matching whole tokens.
- **One long live run.** GSRS returned 502 for about 30 minutes and the run stopped. Retries with backoff and the
  cache (each new attempt starts from what is stored) fixed this.
- **EFSA OpenFoodTox.** Not used. One source (PubChem GHS) keeps the evidence in one format, keyed by the same CIDs.
