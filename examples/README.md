# Worked examples: `label.json` in, `expected.json` out

- `01-simple/` (dsld:60563): one ingredient and four excipients. No claims: "Vegetarian Capsule" names only the capsule.
- `02-blend/` (dsld:78540): a blend header (amount scope `blend`) with two members. One row with three excipients is split into r5.1 to r5.3.
- `03-probiotic/` (dsld:46153): six strains in two groups. Four have a strain-level NCBI id; Lg-36 and Bi-26 get the nearest id and `review`.
