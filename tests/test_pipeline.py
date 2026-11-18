"""Rule tests on real labels, run from the committed cache: python -m unittest

Each test pins one rule that once gave a wrong answer, so a rule change that breaks it shows up here.
"""
import json
import unittest
from functools import lru_cache
from pathlib import Path

from labelwise import fetch
from labelwise.pipeline import process_label
from labelwise.rows import other_ingredient_items

ROOT = Path(__file__).resolve().parent.parent
fetch.offline = True
LABELS = {l["label_id"]: l for l in map(json.loads, open(ROOT / "labels.jsonl", encoding="utf-8")) if l}


@lru_cache(maxsize=None)
def result(label_id):
    return process_label(LABELS[label_id])


def row(label_id, row_id):
    return next(r for r in result(label_id)["rows"] if r["row_id"] == row_id)


def ident(r):
    return (r["identity"] or {}).get("id")


class Rows(unittest.TestCase):
    def test_salt_name_kept_whole(self):
        # the "Magnesium" row name must not cut "magnesium sulfate" down to "sulfate"
        items = other_ingredient_items("Cellulose, magnesium sulfate, vitamin a palmitate", [{"name": "Magnesium"}])
        self.assertEqual(items, ["Cellulose", "magnesium sulfate", "vitamin a palmitate"])
        self.assertEqual(row("retailer:29300", "x10")["verbatim"], "magnesium sulfate")

    def test_repeated_facts_name_removed_at_start(self):
        # a Supplement Facts name repeated before the excipients, with no comma
        items = other_ingredient_items("Vitamin C (as ascorbic acid) Cellulose, silica", [{"name": "Vitamin C"}])
        self.assertEqual(items, ["Cellulose", "silica"])

    def test_as_form(self):
        r = row("retailer:37981", "r16")  # Zinc (as zinc oxide) 5 mg
        self.assertEqual((r["parent"], r["form"]), ("zinc", "zinc oxide"))


class Ids(unittest.TestCase):
    def test_form_gets_the_id(self):
        r = row("retailer:37981", "r16")
        self.assertEqual((r["status"], ident(r)), ("identified", "3007857"))  # zinc oxide, not zinc

    def test_kelp_is_not_astemizole(self):
        # "kelp" is a deep PubChem synonym of the drug astemizole
        r = row("dsld:200021", "r8")
        self.assertEqual((r["status"], r["identity"]), ("review", None))

    def test_amaranth_seed_is_not_the_dye(self):
        r = row("dsld:213195", "r18.1")
        self.assertEqual(r["status"], "review")
        self.assertTrue(r["reason"].startswith("ambiguous_name"))

    def test_vitamin_without_form(self):
        r = row("retailer:24336", "r17")  # Vitamin C 18 mg
        self.assertEqual(r["status"], "review")
        self.assertTrue(r["reason"].startswith("form_not_given"))
        self.assertEqual(ident(r), "54670067")  # nearest id: ascorbic acid

    def test_several_forms(self):
        r = row("retailer:17924", "r4")  # Zinc (as Zinc Picolinate, Citrate)
        self.assertTrue(r["reason"].startswith("multiple_forms"))

    def test_concentrate_gets_nearest_id(self):
        r = row("dsld:241928", "r10")  # Fish Oil concentrate
        self.assertEqual((r["status"], ident(r)), ("review", "XGF7L72M0F"))
        self.assertTrue(r["reason"].startswith("form_no_id"))


class Claims(unittest.TestCase):
    def test_recipe_statement_is_c08(self):
        claims = {c["claim_id"]: c["quote"] for c in result("retailer:19636")["claims"]}
        self.assertEqual(claims.get("C08"), "Formulated without Gluten, GMOs, or Soy")
        self.assertNotIn("C07", claims)  # no gluten ingredients is not a gluten-free test

    def test_vegan_with_animal_row(self):
        notes = [p["note"] for p in result("dsld:241928")["for_a_person"] if p["kind"] == "conflict"]
        self.assertTrue(any("'Vegan'" in n and "r10" in n for n in notes), notes)

    def test_quotes_are_exact(self):
        for label_id in ("retailer:19636", "dsld:241928", "retailer:29300"):
            raw = LABELS[label_id]["raw_text"]
            res = result(label_id)
            for item in res["claims"] + res["candidates"] + res["for_a_person"]:
                self.assertIn(item["quote"], raw)


class Runs(unittest.TestCase):
    def test_same_input_same_output(self):
        self.assertEqual(process_label(LABELS["dsld:241928"]), result("dsld:241928"))

    def test_offline_never_calls_out(self):
        with self.assertRaises(fetch.OfflineMiss):
            fetch.fetch("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/not-in-the-cache/cids/JSON")

    def test_worked_examples(self):
        from check_examples import compare_list, compare_rows
        for ex in sorted((ROOT / "examples").glob("*/label.json")):
            got = process_label(json.loads(ex.read_text()))
            want = json.loads((ex.parent / "expected.json").read_text())
            diffs = compare_rows(got["rows"], want["rows"])
            diffs += compare_list(got["claims"], want["claims"], ["claim_id", "quote", "where"])
            diffs += compare_list(got["evidence"], want["evidence"], ["row_id", "source", "status", "url"])
            self.assertEqual(diffs, [], ex.parent.name)


if __name__ == "__main__":
    unittest.main()
