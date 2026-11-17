# Hand-check marks format

One file per label: `handcheck/premarks/<label_id with ':' -> '_'>.json` (pre-marks) and the final
`marks.json` exported from `review.html` (a list of these objects).

```json
{
  "label_id": "dsld:176258",
  "rows": [
    {"row_id": "r1", "parse": "ok", "identity": "ok", "note": ""}
  ],
  "missed_rows": [{"text": "row on the label that the output does not have", "note": ""}],
  "claims": [{"claim_id": "C07", "mark": "ok", "note": ""}],
  "missed_claims": [{"claim_id": "C10", "quote": "exact label text", "note": ""}],
  "candidates": [{"n": 1, "mark": "ok", "note": ""}],
  "evidence": [{"row_id": "r5", "mark": "ok", "note": ""}]
}
```

Marks are `"ok"` or `"wrong"`. A `note` is required for every `"wrong"` (one short sentence).

## What counts as ok

**Part A, `parse`**: `parent`, `form`, `source`, `strain`, `standardization`, `role`, `group`, `amount`
(value, unit, scope) and `blend_contents` all match what the label says, following `schema.json` and
`examples/`. A split row (r5.1, r5.2) is ok when it names one substance from the original row.

**Part A, `identity`**:
- `identified` rows: ok only if the id is for exactly what the row names (the form when a form is
  given), checked at the source (PubChem / GSRS / NCBI).
- `review` rows: ok if review was the right call (no certain id exists, or the name is ambiguous) and
  the reason is true. A nearest id, if given, must be right for what the reason says it is.
- wrong if an identified id is for something else, or if a certain id was easy to find but the row is
  in review with a false reason.

**Part B**:
- `claims`: ok if the label makes that claim (claims.md definitions and "Not this" column) and the
  quote supports it.
- `missed_claims`: claims.md claims the label makes that the output lacks.
- `candidates`: ok if the text is claim-like, not on the claim list, and not a health statement.

**Part C, `evidence`**: ok if the url is right for the row's id, the status matches the stored copy
(`output/<copy_path>`), and the summary faithfully reflects the copy (no invented or missing hazard
codes). `no_record` is ok only when the copy really has no GHS section.
