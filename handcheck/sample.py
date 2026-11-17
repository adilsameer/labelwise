"""Pick the 20 hand-check labels: 10 DSLD + 10 retailer, fixed seed, examples left out.

python handcheck/sample.py  -> handcheck/sample.json
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = 20261117
EXAMPLES = {json.loads((p / "label.json").read_text())["label_id"] for p in (ROOT / "examples").iterdir() if p.is_dir()}

labels = [json.loads(line)["label_id"] for line in open(ROOT / "labels.jsonl") if line.strip()]
rng = random.Random(SEED)
pick = []
for source in ("dsld", "retailer"):
    pool = sorted(l for l in labels if l.startswith(source + ":") and l not in EXAMPLES)
    pick += sorted(rng.sample(pool, 10))
(ROOT / "handcheck" / "sample.json").write_text(json.dumps({"seed": SEED, "labels": pick}, indent=2) + "\n")
print(pick)
