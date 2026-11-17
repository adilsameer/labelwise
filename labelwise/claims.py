"""Part B: find the claims of claims.md, claim-like candidates, and items for a person.

All rules are the tables at the top of this file. Every quote is cut from raw_text
(raw[start:end]), so it is always an exact substring.
"""
import re

CLAIM_NAMES = {
    "C01": "Vegan", "C02": "Vegetarian", "C03": "Kosher", "C04": "Halal", "C05": "Keto", "C06": "Paleo",
    "C07": "Gluten free", "C08": "No gluten ingredients", "C09": "Wheat free", "C10": "Dairy free",
    "C11": "Soy free", "C12": "Nut free", "C13": "Egg free", "C14": "Shellfish free", "C15": "Sugar free",
    "C16": "No added sugar", "C17": "No artificial colors", "C18": "No artificial flavors",
    "C19": "No artificial preservatives", "C20": "Non-GMO", "C21": "No stearates", "C22": "Organic product",
    "C23": "Made with organic ingredients", "C24": "NSF certified", "C25": "Informed Sport certified",
    "C26": "Third-party tested", "C27": "Made under GMP", "C28": "Made in USA", "C29": "Whole food",
    "C30": "Fermented", "C31": "Enteric coated", "C32": "Chewable", "C33": "For children", "C34": "For women",
    "C35": "Prenatal", "C36": "Contains milk", "C37": "Contains soy", "C38": "Contains fish",
    "C39": "Contains tree nuts", "C40": "Contains gelatin",
}

SHELL = r"(?![- ]?(?:capsules?|caps|softgels?|gelcaps?|shells?|capsule\(s\)))"

# Claims stated directly. claim_id -> (pattern, pattern that cancels a match when it covers it)
POSITIVE = {
    "C01": (r"\bvegans?\b(?:[- ](?:friendly|formula|product))?" + SHELL, None),
    "C02": (r"\bvegetarians?\b(?:[- ](?:friendly|formula|product))?" + SHELL, None),
    "C03": (r"\bkosher\b(?:[- ](?:certified|parve|pareve))?", None),
    "C04": (r"\bhalal\b(?:[- ]certified)?", None),
    "C05": (r"\bketo\b(?:[- ]friendly)?", None),
    "C06": (r"\bpaleo\b(?:[- ]friendly)?", None),
    "C08": (r"\bno gluten ingredients\b", None),
    "C15": (r"\bsugar[- ]free\b|\bzero sugar\b", None),
    "C16": (r"\bno (?:added sugars?|sugar added)\b|\bwithout added sugars?\b", None),
    "C20": (r"(?<!non )(?<!non-)\bnon[- ]?gmo\b(?: project verified)?|\bgmo[- ]free\b", None),
    # "certified organic" alone or "certified organic by X" is the product; "with certified organic, ..." is ingredients
    "C22": (r"\busda organic\b|\bcertified organic\b(?=\s+by\b|\s*[.!]?$)|\b100% organic\b", None),
    "C23": (r"\bmade with organic\b[\w ]*|\borganic ingredients\b|\bwith (?:certified )?organic\b", None),
    "C24": (r"\bnsf\b(?: certified(?: for sport)?)?", r"nsf[- ](?:registered|gmp)|certified [\w-]+(?: [\w-]+)? by nsf|[\w-]+ certified by nsf"),
    "C25": (r"\binformed[- ](?:sport|choice)\b", None),
    "C26": (r"\bthird[- ]party[- ]tested\b|\b(?:independent|third[- ]party) (?:lab|laborator)\w*", None),
    "C27": (r"(?<!non )\bc?gmp\b|\bgood manufacturing practices?\b", None),
    "C28": (r"\b(?:made|manufactured|produced)\s+in\s+(?:the\s+)?(?:u\.?s\.?a?\.?|united states)(?![a-z])"
            r"|\bfacility in the (?:u\.?s\.?a\.?|united states)\b", None),
    "C29": (r"\bwhole[- ]foods?\b", None),
    "C30": (r"\bfermented\b|\bfermentation process\b", None),
    "C31": (r"\benteric[- ]coat(?:ed|ing)\b|\bdelayed[- ]release\b", None),
    "C32": (r"\bchewables?\b|\bchew(?:s|ed)?\b", r"\b(?:not|n't|never)\b[\w ]{0,15}\bchew"),
    "C33": (r"\bfor kids\b|\bkids'?\b|\bchildren'?s\b|\bfor children\b|\bfor toddlers\b",
            r"reach of (?:kids|children)|not (?:intended )?for children|for children (?:under|ages?|aged|\d)"),
    "C34": (r"\bwomen'?s\b|\bfor women\b", None),
    "C35": (r"\bpre-?natal\b|\bfor (?:use )?(?:before|during) pregnancy\b", None),
}

# "Free from / does not contain" list words. item -> claim_id, or ("cand", phrase), or ("unclear", note)
FREE_ITEMS = [
    (r"gluten ingredients", "C08"),
    (r"gluten", "C07"),
    (r"wheat", "C09"),
    (r"dairy|milk|dairy products|milk products|milk derivatives", "C10"),
    (r"soy|soya|soybeans?|soy ingredients|soy products|soy allergens", "C11"),
    (r"eggs?|egg products", "C13"),
    (r"shellfish|shell-fish|crustacean shellfish|crustaceans?", "C14"),
    (r"sugars?", "C15"),
    (r"added sugars?", "C16"),
    (r"(?:artificial |synthetic )?(?:colou?rs?|dyes?|colou?rings?)", "C17"),
    (r"(?:artificial |synthetic )flavou?rs?|(?:artificial |synthetic )flavou?rings?", "C18"),
    (r"(?:artificial |synthetic )?preservatives?", "C19"),
    (r"gmos?|genetically modified organisms|ingredients derived from genetically modified organisms|gmo ingredients", "C20"),
    (r"magnesium stearate|stearates?", "C21"),
    (r"nuts", ("unclear", "'nuts' does not say whether peanuts are included, so Nut free (C12) is not given")),
]
# Free-list words that are claim-like but not on the claim list -> candidates.
CANDIDATE_ITEMS = (r"lactose|yeast|corn|sesame|fish|peanuts?|tree nuts?|salt|sodium|(?:artificial )?sweeteners?|fillers?"
                   r"|binders?|additives|starch|caffeine|bpa|carrageenan|sugar alcohols|refined sugar|fruit juice"
                   r"|animal products|animal|grapefruit|barley|citrus|msg|hexane|chemicals|excipients|fragrances?"
                   r"|artificial ingredients|flavou?rs?|filler ingredients|binders|rice|nightshades|alcohol|bovine|fat")

CLAIMISH = re.compile(r"animal|dairy|milk|gluten|wheat|soy|artificial|gmo|sugar|preservative|filler|additive", re.I)
FREE_TRIGGER = re.compile(r"\b(?:free (?:of|from)(?: synthetic)?|does not contain|do not contain|contains no|contain no"
                          r"|formulated without|made without|with no)\b:?\s*", re.I)
WEAK_TRIGGER = re.compile(r"^no\b\s*", re.I)  # "No soy, wheat or lactose." only at the start of a segment
X_FREE = re.compile(r"\b((?:[A-Za-z][A-Za-z-]*\s*(?:,|&|and)\s*)*[A-Za-z][A-Za-z-]*)[- ]free\b", re.I)
X_FREE_STOP = {"toll", "call", "hassle", "worry"}
X_FREE_CANDIDATES = r"bse|cruelty|allergen|soy-free|grain|nut|peanut|tree nut|dye|fragrance|paraben|sulfate|phthalate"

CONTAINS_TRIGGER = re.compile(r"^(?:allergens?(?: information)?:\s*)?contains:?\s+(?!no\b|less\b|\d|unique|up to)", re.I)
CONTAINS_ITEMS = [
    (r"milk|dairy|whey|casein|milk products", "C36"),
    (r"soy|soya|soybeans?|soy lecithin", "C37"),
    (r"fish|anchovy|sardines?|mackerel|cod|salmon|tuna|tilapia", "C38"),
    (r"tree nuts?|almonds?|cashews?|coconut|walnuts?|pecans?|hazelnuts?|pistachios?|macadamia|brazil nuts?", "C39"),
]

CANDIDATES = [
    r"\bmay contain\b[^.]*",
    r"\b(?:made|manufactured|produced|processed|packaged) in an? [^.]*?facility[^.]*",
    r"\bhypoallergenic\b",
    r"\bplant[- ]based\b",
    r"\b(?:laboratory|lab|clinically|dermatologist|allergy) tested\b",
    r"\btested for (?:purity|potency|quality)\b",
    r"\bguaranteed potency\b",
    r"\bdoes not cause \w+",
    r"\bnon[- ]irritating\b",
    r"\bsustainably sourced\b",
    r"\bwild[- ]caught\b",
    r"\bgrass[- ]fed\b",
    r"\b(?:100% |all[- ])natural\b",
    r"\bsprouted\b",
    r"\bcertified b corporation\b",
    r"\bfda[- ]registered facility\b",
    r"\bthird[- ]party audited\b",
    r"\bcertified [\w-]+(?: [\w-]+)? by nsf\b",
    r"\b[\w-]+ certified by nsf\b",
    r"\bscreened for heavy metals\b",
    r"\bnot (?:made|manufactured|produced) with\b[^.]*",  # a recipe statement, not Free-from (claims.md C09)
    r"\bno animal/dairy[^.]*",
]

UNCLEAR = [
    (r"\bhala\b", "'Hala' may be a misspelling of 'Halal'; check the label"),
    (r"\bnon[- ]gmp project verified\b", "'Non GMP Project Verified' may be a misspelling of 'Non GMO Project Verified'"),
]

# Ingredient words for the conflict checks (matched on parsed rows).
ANIMAL = r"gelatin|\bfish\b|bovine|porcine|beef|pork|chicken|anchov|sardine|\bcod\b|salmon|tuna|krill|shellfish|carmine|cochineal|collagen|chondroitin|lanolin|shark"
ANIMAL_NOT_VEGAN = ANIMAL + r"|(?<!coconut )\bmilk\b(?! thistle)|whey|casein|lactose|beeswax|honey|\begg|colostrum"
FREE_FROM_ROWS = {
    "C10": (r"(?<!coconut )\bmilk\b(?! thistle)|whey|casein|lactose|butter|cream|yogurt", "C36"),
    "C11": (r"\bsoy|glycine (?:soja|max)", "C37"),
    "C07": (r"\bwheat\b(?!grass)|barley|\brye\b", None),
    "C09": (r"\bwheat\b(?!grass)", None),
    "C13": (r"\begg", None),
    "C14": (r"shrimp|crab|lobster|krill|chitosan|shellfish", None),
    "C12": (r"almond|cashew|walnut|pecan|hazelnut|pistachio|macadamia|peanut", "C39"),
}

SEGMENT_SPLIT = re.compile(r"\n+|(?<=[.!?])\s+(?=[A-Z0-9(])|\s+-\s+(?=\S)|\s*;\s*|\s*~\s*|\s+\|\s+|\s{2,}")


# ---------------------------------------------------------------- text helpers

def segments(raw):
    """(start, end) spans of short statements: lines, sentences, bullet items."""
    out, pos = [], 0
    for m in list(SEGMENT_SPLIT.finditer(raw)) + [None]:
        end = m.start() if m else len(raw)
        s, e = pos, end
        while s < e and raw[s] in " -•\t":
            s += 1
        while e > s and raw[e - 1] in " \t":
            e -= 1
        if e > s:
            out.append((s, e))
        pos = m.end() if m else len(raw)
    return out


def ingredient_blocks(label):
    """Spans of raw_text that list ingredients (claims there are ingredient names, not product claims)."""
    raw, spans = label["raw_text"], []
    for m in re.finditer(r"Supplement Facts\n.*?(?=\n\n|$)", raw, re.S):
        spans.append((m.start(), m.end()))
    for m in re.finditer(r"Other Ingredients:.*?(?=\n\n|$)", raw, re.S):
        spans.append((m.start(), m.end()))
    other = (label.get("other_ingredients") or "").strip()
    if other:
        for m in re.finditer(re.escape(other), raw):
            spans.append((m.start(), m.end()))
    return spans


def inside(pos, spans):
    return any(s <= pos < e for s, e in spans)


def where(label, quote):
    fields = [
        ("title", label.get("title") or ""),
        ("serving", label.get("serving") or ""),
        ("statements", "\n".join(s["text"] for s in label.get("statements") or [])),
        ("other_ingredients", label.get("other_ingredients") or ""),
        ("rows", "\n".join(r["verbatim"] for r in label.get("rows") or [])),
    ]
    return next((name for name, text in fields if quote in text), "raw_text")


def norm_phrase(text):
    return re.sub(r"\s+", " ", text.lower()).strip(" .,;:")


def short_noun(item):
    """A free-list item we can name: up to 3 words, no verbs, no slash."""
    return (len(item.split()) <= 3 and "/" not in item
            and not re.search(r"\b(?:is|are|be|was|were|tested|suitable|manufactured|made|produced|for|with)\b", item))


def split_items(text):
    text = re.sub(r"\([^)]*\)", "", text)
    parts = re.split(r",|\bor\b|\band\b|\bnor\b|&", text, flags=re.I)
    return [p.strip(" .:;*") for p in parts if p.strip(" .:;*")]


# ---------------------------------------------------------------- finder

class Finder:
    def __init__(self, label, rows):
        self.label, self.rows, self.raw = label, rows, label["raw_text"]
        self.claims = {}       # claim_id -> (start, end)
        self.exceptions = []   # (claim_id, start, end)
        self.candidates = []   # (start, phrase, quote)
        self.unclear = []      # (start, note, quote)
        self.text_exceptions = []  # (start, note, quote): claim-like text with "except"
        self.blocks = ingredient_blocks(label)

    def add_claim(self, cid, start, end, seg):
        s, e = seg
        if re.search(r"\bexcept\b", self.raw[s:e], re.I):
            self.exceptions.append((cid, s, e))
            return
        if cid not in self.claims or start < self.claims[cid][0]:
            self.claims[cid] = (start, end)

    def add_candidate(self, start, phrase, quote_span):
        self.candidates.append((start, norm_phrase(phrase), self.raw[quote_span[0]:quote_span[1]].strip()))

    def run(self):
        for seg in segments(self.raw):
            if inside(seg[0], self.blocks):
                continue
            self.positive(seg)
            self.free_lists(seg)
            self.x_free(seg)
            self.contains(seg)
            self.candidate_patterns(seg)
            self.unclear_patterns(seg)
        self.title_organic()
        self.gelatin()
        if "C22" in self.claims:
            self.claims.pop("C23", None)  # the whole product is organic
        if "C07" in self.claims:
            self.claims.pop("C08", None)

    def positive(self, seg):
        s, e = seg
        text = self.raw[s:e]
        for cid, (pat, cancel) in POSITIVE.items():
            for m in re.finditer(pat, text, re.I):
                if cancel and any(c.start() <= m.start() < c.end() or m.start() <= c.start() < m.end()
                                  for c in re.finditer(cancel, text, re.I)):
                    continue
                if cid == "C33" and re.search(r"(reach of|not (intended )?for)\s*$", text[:m.start()], re.I):
                    continue
                self.add_claim(cid, s + m.start(), s + m.end(), seg)
                break

    def free_lists(self, seg):
        s, e = seg
        text = self.raw[s:e]
        m = FREE_TRIGGER.search(text) or WEAK_TRIGGER.match(text)
        if not m:
            return
        weak = m.re is WEAK_TRIGGER
        items = split_items(text[m.end():])
        mapped, unmapped, artificial = [], [], False
        for item in items:
            low = item.lower()
            low = re.sub(r"^(?:any|no)\s+", "", low)  # "No gluten, no wheat, ..."
            if low.startswith("added ") and not re.match(r"added sugars?$", low):
                low = low[len("added "):]  # "no added milk" -> milk
            if re.match(r"(artificial|synthetic)\b", low):
                artificial = True
            elif artificial and re.fullmatch(r"flavou?rs?|colou?rs?|sweeteners?|preservatives?", low):
                low = "artificial " + low
            hit = next((t for p, t in FREE_ITEMS if re.fullmatch(p, low)), None)
            if hit:
                mapped.append((low, hit))
            elif re.fullmatch(CANDIDATE_ITEMS, low):
                mapped.append((low, ("cand", f"no {low}")))
            elif short_noun(low):
                unmapped.append(low)
            elif weak:
                # "No animal/dairy or plant source probiotic cultures": not a clean list, keep it whole
                if mapped or unmapped or CLAIMISH.search(text):
                    self.add_candidate(s, text, seg)
                return
            else:
                break  # the list has ended: "... additives, and are manufactured in ..."

        quote_start = s + m.start()
        quote_end = e - (1 if self.raw[e - 1] == "." else 0)
        names = {low for low, _ in mapped}
        tree, peanut = any(n.startswith("tree nut") for n in names), any(n.startswith("peanut") for n in names)
        if tree and peanut:
            self.add_claim("C12", quote_start, quote_end, seg)
        for low, hit in mapped:
            if isinstance(hit, str):
                self.add_claim(hit, quote_start, quote_end, seg)
            elif hit[0] == "unclear" and not (tree and peanut):
                self.unclear.append((s, hit[1], self.raw[quote_start:quote_end]))
            elif hit[0] == "cand" and not ((tree and peanut) and re.match(r"(tree nut|peanut)", low)):
                self.candidates.append((s, hit[1], self.raw[quote_start:quote_end]))
        if weak and not mapped and not CLAIMISH.search(text):
            return  # "No refrigeration required" is not a free-from list
        for low in unmapped:
            self.candidates.append((s, f"no {low}", self.raw[quote_start:quote_end]))

    def x_free(self, seg):
        s, e = seg
        text = self.raw[s:e]
        for m in X_FREE.finditer(text):
            words = [w.lower() for w in split_items(m.group(1))]
            if not words or words[-1] in X_FREE_STOP:
                continue
            known = []
            for w in reversed(words):  # read back from "free": "Collection, Caffeine Free" -> caffeine only
                w = re.sub(r"^(?:certified|naturally|100%)\s+", "", w)
                hit = next((t for p, t in FREE_ITEMS if re.fullmatch(p, w)), None)
                if hit is None and not re.fullmatch(CANDIDATE_ITEMS + "|" + X_FREE_CANDIDATES, w):
                    break
                known.append((w, hit))
            if not known:
                continue
            first = min(m.start() + m.group(0).lower().find(w) for w, _ in known if w in m.group(0).lower())
            span = (s + first, s + m.end())
            for w, hit in known:
                if isinstance(hit, str):
                    self.add_claim(hit, span[0], span[1], seg)
                elif hit:
                    self.unclear.append((s, hit[1], self.raw[span[0]:span[1]]))
                else:
                    self.add_candidate(s, f"{w} free", span)

    def contains(self, seg):
        s, e = seg
        text = self.raw[s:e]
        m = CONTAINS_TRIGGER.match(text)
        if not m:
            return
        quote_end = e - (1 if self.raw[e - 1] == "." else 0)
        for item in split_items(text[m.end():]):
            low = re.sub(r"\s+(?:ingredients|products)$", "", item.lower())
            hit = next((t for p, t in CONTAINS_ITEMS if re.fullmatch(p, low)), None)
            if hit:
                self.add_claim(hit, s, quote_end, seg)

    def candidate_patterns(self, seg):
        s, e = seg
        text = self.raw[s:e]
        for pat in CANDIDATES:
            for m in re.finditer(pat, text, re.I):
                a = s + m.start()
                if any(cs <= a < ce for cs, ce in self.claims.values()):
                    continue
                if re.search(r"\bexcept\b", m.group(0), re.I):
                    self.text_exceptions.append((s, "The statement has an exception; a person must decide what it covers.",
                                                 self.raw[s + m.start():s + m.end()].strip()))
                    continue
                self.add_candidate(s, m.group(0), seg)

    def unclear_patterns(self, seg):
        s, e = seg
        text = self.raw[s:e]
        for pat, note in UNCLEAR:
            m = re.search(pat, text, re.I)
            if m:
                self.unclear.append((s, note, m.group(0)))

    def title_organic(self):
        title = self.label.get("title") or ""
        m = re.match(r"organic\b", title, re.I)
        if m and title in self.raw:
            start = self.raw.find(title)
            if not inside(start, self.blocks):
                self.add_claim("C22", start, start + m.end(), (start, start + len(title)))

    def gelatin(self):
        for m in re.finditer(r"\bgelatin\b", self.raw, re.I):
            around = self.raw[max(0, m.start() - 12):m.end() + 6].lower()
            if re.search(r"gelatin[- ]free|no gelatin|without gelatin|free of gelatin", around):
                continue
            self.add_claim("C40", m.start(), m.end(), (m.start(), m.end()))
            return


# ---------------------------------------------------------------- conflicts

def row_text(row):
    text = " ".join(x for x in (row["verbatim"], row["parent"], row["source"]) if x).lower()
    return re.sub(r"\b[\w-]+[- ]free\b", " ", text)  # "shell-fish free glucosamine" is not shellfish


def conflicts(finder, claims):
    found = []
    by_id = {c["claim_id"]: c for c in claims}
    rows = [r for r in finder.rows if r["role"] != "blend_header"]

    def first_row(pattern):
        return next((r for r in rows if re.search(pattern, row_text(r))), None)

    for cid, pattern in (("C01", ANIMAL_NOT_VEGAN), ("C02", ANIMAL)):
        if cid in by_id:
            r = first_row(pattern)
            if r:
                found.append(("conflict", f"The label says '{by_id[cid]['quote']}', but row {r['row_id']} "
                              f"'{r['verbatim']}' is from an animal.", by_id[cid]["quote"]))
            for other in ("C36", "C38", "C40") if cid == "C01" else ("C38", "C40"):
                if other in by_id and not r:
                    found.append(("conflict", f"The label says '{by_id[cid]['quote']}' and also "
                                  f"'{by_id[other]['quote']}' ({CLAIM_NAMES[other]}).", by_id[cid]["quote"]))
                    break

    for cid, (pattern, contains_id) in FREE_FROM_ROWS.items():
        if cid not in by_id:
            continue
        if contains_id and contains_id in by_id:
            found.append(("conflict", f"The label says '{by_id[cid]['quote']}' and also "
                          f"'{by_id[contains_id]['quote']}'.", by_id[cid]["quote"]))
            continue
        r = first_row(pattern)
        if r:
            found.append(("conflict", f"The label says {CLAIM_NAMES[cid]} ('{by_id[cid]['quote']}'), "
                          f"but row {r['row_id']} is '{r['verbatim']}'.", by_id[cid]["quote"]))

    if "C15" in by_id:
        for r in finder.rows:
            if re.fullmatch(r"(total )?sugars?", r["parent"] or "") and (r["amount"]["value"] or 0) > 0:
                found.append(("conflict", f"The label says '{by_id['C15']['quote']}', but row {r['row_id']} "
                              f"'{r['verbatim']}' shows sugar.", by_id["C15"]["quote"]))
                break
    return found


# ---------------------------------------------------------------- entry

def find_claims(label, rows):
    """Return (claims, candidates, for_a_person) for one label."""
    f = Finder(label, rows)
    f.run()
    raw = f.raw

    claims = []
    for cid in sorted(f.claims):
        s, e = f.claims[cid]
        quote = raw[s:e].strip()
        claims.append({"claim_id": cid, "claim": CLAIM_NAMES[cid], "quote": quote, "where": where(label, quote)})

    people = []
    for cid, s, e in f.exceptions:
        if cid not in f.claims:
            people.append(("exception", f"{CLAIM_NAMES[cid]} is stated with an exception; a person must decide.",
                           raw[s:e].strip()))
    people += [("exception", note, quote) for _, note, quote in sorted(f.text_exceptions)]
    people += [("unclear", note, quote) for _, note, quote in sorted(f.unclear)]
    people += conflicts(f, claims)
    seen, for_a_person = set(), []
    for kind, note, quote in people:
        if (kind, note) not in seen:
            seen.add((kind, note))
            for_a_person.append({"kind": kind, "note": note, "quote": quote})

    seen, candidates = set(), []
    for start, phrase, quote in sorted(f.candidates, key=lambda c: (c[0], c[1])):
        if phrase in seen:
            continue
        seen.add(phrase)
        candidates.append({"phrase": phrase, "quote": quote})
    return claims, candidates, for_a_person
