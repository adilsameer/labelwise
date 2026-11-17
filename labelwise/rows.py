"""Part A, step 1: split label rows and parse each one into its fields.

No lookups happen here. Each row also carries internal hints (keys that
start with "_") for the lookup step; they are removed before output.
"""
import re

from labelwise import rules

MARKS = re.compile(r"\((?:R|TM|r|tm|SM)\)|[®™℠†‡*♦♢]|#(?!\s*\d)")
TAG = re.compile(r"\b(PlantPart|Genus|Species|Note|Form|Alt\. Name):")

NUTRITION = re.compile(
    r"(calories( from fat)?|calories/energy|energy|total fat|fat|saturated fat|trans fat"
    r"|(poly|mono)unsaturated fat|total carbohydrates?|carbohydrates?|nutrition facts.*"
    r"|(total |soluble |insoluble )?dietary fiber|(soluble |insoluble )?fiber"
    r"|total sugars?|sugars?|added sugars|includ(?:es|ed) .*added sugars|sugar alcohols?|protein)",
    re.I,
)

MICROBE_GENERA = {
    "lactobacillus", "lacticaseibacillus", "lactiplantibacillus", "limosilactobacillus",
    "ligilactobacillus", "bifidobacterium", "streptococcus", "lactococcus", "bacillus",
    "saccharomyces", "pediococcus", "leuconostoc", "enterococcus", "akkermansia",
    "clostridium", "weizmannia", "heyndrickxia",
}

# Nutrient names that are already one compound: no form is needed to identify them.
SPECIFIC_NUTRIENT = re.compile(r"folic acid|riboflavin|biotin|vitamin d[23]|vitamin d-[23]|vitamin k[12]|niacinamide|nicotinic acid")

# Vitamins and minerals: a bracket after these names is a chemical form.
NUTRIENT = re.compile(
    r"(vitamin [a-k][0-9]*|vitamin b-?[0-9]+|thiamine?|riboflavin|niacin|folate|folic acid|biotin"
    r"|pantothenic acid|calcium|iron|magnesium|zinc|selenium|copper|manganese|chromium"
    r"|molybdenum|iodine|potassium|sodium|phosphorus|boron|chloride|vanadium|silicon)",
    re.I,
)

PLANT_PARTS = (
    "aerial parts", "whole plant", "fruiting bodies", "fruiting body", "root", "roots", "leaf",
    "leaves", "seed", "seeds", "bark", "fruit", "berry", "berries", "flower", "flowers", "herb",
    "rhizome", "stem", "peel", "bulb", "mycelium", "kernel", "hull", "sprout", "resin", "bran",
    "needle", "cone", "husk", "pod", "tuber", "kidney", "primordia",
)
PLANT_PART_RE = re.compile(r"\b(" + "|".join(PLANT_PARTS) + r")\b", re.I)
PHYSICAL_FORM_RE = re.compile(r"\b(extract powder|extract|powder|juice concentrate|concentrate|isolate|hydrolysate|oil)\b", re.I)
SOURCE_PREFIX_RE = re.compile(r"^(vegetable|vegetarian|plant-derived|plant|bovine|porcine|marine|fish|chicken)\s+", re.I)
DESCRIPTORS_RE = re.compile(
    r"\b(organic|wildcrafted|natural|standardized|pure|purified|raw|whole|premium|dried|fresh"
    r"|certified|non-gmo|grassfed|grass-fed|modified|deionized|gluten[- ]free)\b",
    re.I,
)
EXCIPIENT_WRAPPER_RE = re.compile(
    r"capsule|softgel|shell|coating|may contain|one or more|ingredients|tablet|enzymes|blend|complex|gel\b"
    r"|less than|or less of|contains", re.I)
BLEND_WORD_RE = re.compile(r"blend|complex|formula|matrix", re.I)
INLINE_BLEND_RE = re.compile(r"^([^()]*?(?:blend|complex|formula))[\s:(]*(.+)$", re.I)
LEADING_COUNT_RE = re.compile(r"^\d[\d.,]*\s*(?i:billion|million)?\s*(?i:cfu(?:\s*/\s*serving)?)[^A-Z]*")
STRAIN_RE = re.compile(r"\b([A-Z]{1,4}[a-z]{0,2}-?\d{1,6}[A-Za-z]?|[A-Z]{3,6}|\d{3,6})\b")
NOT_STRAIN = {"HDS", "CFU", "DSM", "ATCC"}
AMOUNT_RE = re.compile(r"\s+(\d[\d,]*(?:\.\d+)?)\s*(mg|mcg|µg|g|iu)\.?$", re.I)


def clean(text):
    return re.sub(r"\s+", " ", MARKS.sub("", text)).strip(" ,.;:")


def split_top_level(text):
    """Split on commas that are not inside brackets."""
    parts, depth, cur = [], 0, ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    out = []
    for p in parts:
        p = re.sub(r"^\s*(&|and)\s+", "", p.strip()).strip(" .")
        if p:
            out.append(p)
    return out


def bracket_list(text):
    """'Head (a, b, c)' -> ('Head', [a, b, c]) when the bracket holds a list."""
    m = re.match(r"^(.*?)[\s:]*[(\[](.*)[)\]]?\s*$", text)
    if not m:
        return None
    head, inner = m.group(1), m.group(2).rstrip(")]")
    items = split_top_level(inner)
    return (head, items) if len(items) > 1 else None


def nutrient_head(name):
    return bool(NUTRIENT.fullmatch(clean(re.split(r"[(\[]", name)[0]).lower()))


def is_nutrition(name):
    return bool(NUTRITION.fullmatch(clean(name).lower().strip()))


# ---------------------------------------------------------------- fields

TRAILING_AMOUNT_RE = re.compile(
    r"(\s+[<>]?\d[\d,]*(?:\.\d+)?\s*(?:[A-Za-zµ]+(?:\(s\))?)?(?:\s+(?:RAE|DFE|NE|DV))?)+\s*$")
SALT_RE = re.compile(r"(ate|ite|ide|hcl)\b", re.I)
COMPOUND_HEAD_RE = re.compile(r"\b\w*(ase|ine|acid|ate|ide|hcl)\b", re.I)


def strip_amount(text):
    return TRAILING_AMOUNT_RE.sub("", text)


def tag_value(verbatim, tag):
    if tag in ("Genus", "Species"):
        m = re.search(rf"\b{tag}:\s*([A-Za-z-]+)", verbatim)
        return m.group(1) if m else None
    if tag == "PlantPart":
        m = re.search(r"\bPlantPart:\s*(" + "|".join(PLANT_PARTS) + r"|\S+)", verbatim, re.I)
        return m.group(1) if m else None
    m = re.search(rf"\b{re.escape(tag)}:\s*(.+?)(?=\s+\b(?:PlantPart|Genus|Species|Note|Form|Alt\. Name):|\)|$)", verbatim)
    return m.group(1).strip() if m else None


def chemical_form(name, verbatim, head_is_nutrient):
    for text in (verbatim, name):
        m = re.search(r"\((?:Form:[^()]*?)?\bas ([^()]+?)(?:\s+from [^()]+)?\)", text, re.I) or \
            re.search(r"\bForm:[^()]*?\bas ([^()]+?)(?=\s+\b(?:Note|Alt\. Name|PlantPart):|\)|$)", text)
        if m:
            return form_text(m.group(1))
    # "from X" is a form when X is a salt of a nutrient or names the ingredient itself
    # ("Choline (Form: from Choline Bitartrate)", "Thiamin (from Thiamin HCl)"); otherwise it is a source
    head = clean(re.split(r"[(\[]", strip_brands(name))[0]).lower()
    for text in (verbatim, name):
        m = re.search(r"(?:\bForm:\s*|\()from ([^()]+?)(?=\s+\b(?:Note|Alt\. Name|PlantPart):|\)|$)", text)
        if m and (head_is_nutrient and SALT_RE.search(m.group(1)) or head and head.split()[-1] in m.group(1).lower()):
            return form_text(m.group(1))
    if head_is_nutrient:
        for text in (name, verbatim):
            m = re.search(r"^[^(]+\(([^()]+)\)", MARKS.sub("", text))
            if m and not PLANT_PART_RE.fullmatch(m.group(1).strip()) \
                    and not re.match(r"(from|form|alt)\b", m.group(1), re.I) \
                    and not re.match(r"vitamin\b", m.group(1), re.I):
                return form_text(m.group(1))
    return None


def form_text(text):
    """Clean a form: no brand words, no leading amount ("400 mcg folic acid")."""
    text = clean(strip_brands(text))
    text = re.sub(r"^\d[\d.,]*\s*(mg|mcg|µg|g|iu)\s+", "", text, flags=re.I)
    words = [w for w in text.split() if w.lower() not in rules.BRAND_WORDS]
    return " ".join(words).lower() or None


def standardization(verbatim):
    verbatim = strip_amount(verbatim)
    m = re.search(r"standardized to ([^()\[\]]+)", verbatim, re.I)
    if m:
        return clean(re.sub(r"^contain(s|ing)?\s+", "", m.group(1).strip(), flags=re.I))
    found = re.findall(r"\d+(?:\.\d+)?\s*%\s*[A-Za-z][A-Za-z\- ]*[A-Za-z]", verbatim)
    found += [f"{a} [{b}]" for a, b in re.findall(r"([A-Za-z]+ \d[\d.]*\s*mg)\s*\[(\d+(?:\.\d+)?%)\]", verbatim)]
    found += re.findall(r"\b\d+:1\b", verbatim)
    return "; ".join(clean(f) for f in found) or None


def latin_binomial(name):
    m = re.search(r"\(([A-Z][a-z]+ [a-z]+(?: (?:var|subsp)\. [a-z]+)?)\)", name)
    return m.group(1).lower() if m else None


def strip_brands(text):
    text = re.sub(r"\S+\s*(?:®|™|\((?:R|TM)\))", " ", text)
    words = text.split()
    if len(words) >= 3 and re.fullmatch(r"[A-Z][A-Z0-9-]{2,}", words[0]) and not words[1].startswith("("):
        words = words[1:]
    return " ".join(words)


def parse_substance(name, verbatim):
    """Parse one substance name into parent/form/source/standardization + lookup hints."""
    base = strip_brands(name)
    head = clean(re.split(r"[(\[]", base)[0])
    head = re.sub(r"\s\d[\d,.]*(\s+[A-Z]{2,})+", "", head)  # potency: "Lactase 9,000 FCC ALU"
    head_is_nutrient = bool(NUTRIENT.fullmatch(head.lower()))

    form = chemical_form(name, verbatim, head_is_nutrient)
    latin = latin_binomial(base)
    genus, species = tag_value(verbatim, "Genus"), tag_value(verbatim, "Species")
    if not latin and genus and species:
        latin = f"{genus} {species}".lower()

    sources = []
    part = tag_value(verbatim, "PlantPart")
    for m in re.finditer(r"\(([^()]+)\)", base):
        inner = m.group(1).strip()
        if PLANT_PART_RE.fullmatch(inner.lower()):
            sources.append(inner.lower())
        elif re.fullmatch(r"[A-Za-z ,]+", inner) and PLANT_PART_RE.search(inner) and not latin_binomial(m.group(0)):
            sources.append(", ".join(p.lower() for p in PLANT_PART_RE.findall(inner)))
    for text in (name, verbatim):
        m = re.search(r"\bfrom ([^()]+?)(?=\s+\b(?:Note|Alt\. Name|PlantPart|Genus):|\)|$)", strip_amount(text), re.I)
        if m and not re.match(r"\d", m.group(1)) and clean(m.group(1)).lower() != form:
            sources.append(clean(m.group(1)).lower())
            break
    m = SOURCE_PREFIX_RE.match(head)
    if m and PHYSICAL_FORM_RE.sub("", head[m.end():]).strip():  # "Fish Oil" keeps "fish": "oil" alone is no substance
        sources.insert(0, m.group(1).lower())
        head = head[m.end():]
    # plant parts written outside brackets: "oryza sativa (rice) bran extract"
    in_head = PLANT_PART_RE.findall(re.sub(r"\([^()]*\)", " ", base))
    if part:
        sources.insert(0, part.lower())
    sources += [p.lower() for p in in_head]

    phys = PHYSICAL_FORM_RE.search(name)
    if not form and phys and not head_is_nutrient:
        form = phys.group(1).lower()

    parent = PLANT_PART_RE.sub(" ", head)
    parent = PHYSICAL_FORM_RE.sub(" ", parent) if phys and phys.group(1).lower() != "oil" or not parent else parent
    parent = clean(DESCRIPTORS_RE.sub(" ", parent)).lower()
    parent = re.sub(r"\d+(?:\.\d+)?\s*%", " ", parent)
    parent = re.sub(r"(?<=\w)\s+(capsules?|softgels?|shells?)$", "", parent.strip())  # "gelatin capsule"
    parent = re.sub(r"\s+", " ", parent).strip(" ,-/")
    common = parent
    if latin and COMPOUND_HEAD_RE.search(parent or ""):
        sources.append(latin)  # "Lactase (Aspergillus oryzae)": the organism is the source
        latin = None
    elif latin:
        parent = latin
    if not parent:
        parent = clean(DESCRIPTORS_RE.sub(" ", head)).lower() or clean(name).lower()

    names = []
    alt = tag_value(verbatim, "Alt. Name")
    synonyms = [clean(x).lower() for x in re.findall(r"\(([^()]+)\)", base)
                if not PLANT_PART_RE.search(x) and not re.match(r"(as|from|form|alt\.|standardized)\b", x, re.I)
                and not re.search(r"\d", x)]
    for n in (form, parent, latin, clean(alt).lower() if alt else None, clean(head).lower(), *synonyms):
        if n and n not in names:
            names.append(n)
    seen, source_list = set(), []
    for s in sources:
        if s not in seen:
            seen.add(s)
            source_list.append(s)
    return {
        "parent": parent,
        "form": form,
        "source": ", ".join(source_list) or None,
        "standardization": standardization(verbatim),
        "_names": names,
        "_multi_form": bool(form and re.search(r",|&| and ", form)),
        "_nutrient": head_is_nutrient and not SPECIFIC_NUTRIENT.fullmatch(head.lower()),
        "_latin": latin,
        "_common": common or None,
        "_parts": [p.lower() for p in PLANT_PART_RE.findall(" ".join(source_list))],
        "_physical": phys.group(1).lower() if phys else None,
        "_organic": bool(re.search(r"\borganic\b", name, re.I)),  # farm produce, never a synthetic chemical
    }


def parse_microbe(name):
    words = [w.strip(",;()") for w in clean(name).split()]
    words = [w for w in words if w]
    genus = words[0].lower()
    rest = words[1:]
    species = []
    if rest and re.fullmatch(r"[a-z]+", rest[0]):
        species.append(rest.pop(0))
        if rest and rest[0] in ("subsp.", "ssp.", "var."):
            rest.pop(0)
        if rest and re.fullmatch(r"[a-z]{3,}", rest[0]) and rest[0] not in ("strain", "is", "and"):
            species += ["subsp.", rest.pop(0)]
    tail = " ".join(rest)
    strain = next((s for s in STRAIN_RE.findall(tail) if s not in NOT_STRAIN), None)
    parent = " ".join([genus] + species).lower()
    return {
        "parent": parent,
        "form": None,
        "source": None,
        "standardization": None,
        "strain": strain,
        "_names": [parent],
        "_multi_form": False,
    }


def is_microbe(name):
    first = clean(name).split(" ")[0].lower() if clean(name) else ""
    return first in MICROBE_GENERA and len(clean(name).split()) >= 2


# ---------------------------------------------------------------- rows

FUNCTION_WORD_RE = re.compile(r"^(?:colou?r|colou?ring|anti-?caking agent|emulsifier|thickener|stabili[sz]er|glazing agent"
                              r"|sweetener|preservative|antioxidant|acidity regulator|humectant)\s*[(\[]([^()\[\]]+)[)\]]$", re.I)


def make_row(row_id, verbatim, name, role, group, amount, unit, blend_contents=None):
    row = {
        "row_id": row_id,
        "verbatim": clean_verbatim(verbatim),
        "parent": None, "form": None, "source": None, "strain": None, "standardization": None,
        "role": role,
        "group": group,
        "amount": {
            "value": amount,
            "unit": unit,
            "scope": {"ingredient": "ingredient", "blend_header": "blend", "blend_member": "member"}.get(role),
        },
        "blend_contents": blend_contents,
        "identity": None,
        "status": "review",
        "reason": None,
        "_kind": "substance",
        "_names": [],
        "_multi_form": False,
    }
    fn = FUNCTION_WORD_RE.match(clean(name)) or FUNCTION_WORD_RE.match(clean(strip_amount(verbatim)))
    if fn:  # "Color (Titanium Dioxide)": the bracket names the substance
        name = verbatim = fn.group(1)
    if role == "blend_header":
        row["_kind"] = "blend"
        row["reason"] = ("blend_header: group name inside the blend; the member rows carry the ids" if group
                         else "blend_header: named mixture; the member rows carry the ids")
        if blend_contents == "not_disclosed":
            row["reason"] = "blend_header: named mixture; the label does not list the members"
    elif is_nutrition(name) and role != "excipient":
        row["_kind"] = "nutrition"
        row["parent"] = clean(name).lower()
        row["reason"] = "nutrition_panel: a nutrition facts line, not one substance"
    elif is_microbe(name):
        row["_kind"] = "microbe"
        row.update(parse_microbe(name))
    else:
        row.update(parse_substance(name, verbatim))
    return row


def clean_verbatim(text):
    return re.sub(r"\s+", " ", text).strip() or text


def build_rows(label):
    if not label["rows"]:
        return rows_from_raw_text(label["raw_text"])

    src = label["rows"]
    by_id = {r["row_id"]: r for r in src}
    has_members = {r["group"] for r in src if r["group"]}
    out = []
    for r in src:
        name, verbatim = r["name"], r["verbatim"]
        group = r["group"]
        # Children of a nutrition line (Total Fat -> Saturated Fat) are not blend members.
        # Children of a nutrition line (Total Fat -> Saturated Fat) or of a nutrient
        # ("Folate (Folic Acid)" -> "Folic Acid") are not blend members.
        if group and group in by_id and (is_nutrition(by_id[group]["name"]) or nutrient_head(by_id[group]["name"])):
            group = None

        if r["section"] == "other_ingredients":
            split = bracket_list(verbatim)
            if split and EXCIPIENT_WRAPPER_RE.search(split[0]):
                head_parts = [p.lower() for p in PLANT_PART_RE.findall(split[0])]  # "Sprouted seed Complex (...)"
                for i, item in enumerate(split[1], 1):
                    member = make_row(f"{r['row_id']}.{i}", item, item, "excipient", None, None, None)
                    if head_parts and member["_kind"] == "substance" and not member["_parts"]:
                        member["_parts"] = head_parts
                        member["source"] = ", ".join(filter(None, [member["source"], *head_parts]))
                    out.append(member)
                continue
            row = make_row(r["row_id"], verbatim, name, "excipient", None, r["amount"], r["unit"])
            if split:  # "Fish Gelatin (Carp, Catfish, ...)": one substance, the list is its source
                row["source"] = ", ".join(clean(x).lower() for x in split[1])
            row["amount"]["scope"] = None
            out.append(row)
            continue

        nutrition = is_nutrition(name)
        members = None
        for text in ([] if nutrition else [clean(name), clean(strip_amount(verbatim))]):
            inline = INLINE_BLEND_RE.match(text)
            if inline:
                parts = split_top_level(LEADING_COUNT_RE.sub("", inline.group(2)).rstrip(")"))
                if len(parts) > 1:
                    members = parts
                    break

        if r["row_id"] in has_members and not nutrition and not nutrient_head(name):
            role, contents = "blend_header", "listed"
        elif members:
            role, contents = "blend_header", "listed"
        elif BLEND_WORD_RE.search(re.split(r"\(", name)[0]) and not nutrition and not NUTRIENT.match(name):
            role, contents = "blend_header", "not_disclosed"
        elif group:
            role, contents = "blend_member", None
        else:
            role, contents = "ingredient", None

        out.append(make_row(r["row_id"], verbatim, name, role, group, r["amount"], r["unit"], contents))
        for i, item in enumerate(members or [], 1):
            out.append(make_row(f"{r['row_id']}.{i}", item, item, "blend_member", r["row_id"], None, None))

    # Retailer labels give other ingredients only as text: make them rows x1, x2, ...
    if not any(r["section"] == "other_ingredients" for r in src) and (label.get("other_ingredients") or "").strip():
        for text in other_ingredient_items(label["other_ingredients"], src):
            row = make_row(f"x{sum(1 for o in out if o['row_id'].startswith('x')) + 1}", text, text,
                           "excipient", None, None, None)
            row["amount"]["scope"] = None
            out.append(row)
    return out


ALLERGEN_SENTENCE_RE = re.compile(r"^(?:milk|tree nuts?|soy|wheat|eggs?|fish|shellfish|peanuts?|sesame|none)\b|^contains\s*:", re.I)
LIST_PREFIX_RE = re.compile(r"^(?:contains\s*)?(?:<\s*2%|less than 2%(?: of)?|2% or less of)\s*:?\s*", re.I)


def other_ingredient_items(text, rows):
    """Split a retailer other-ingredients text into one item per substance."""
    # the text sometimes repeats a Supplement Facts row before the excipients, with no comma
    for r in rows:
        name = clean(r["name"])
        if len(name) <= 5 or BLEND_WORD_RE.search(name):
            continue
        found = re.search(r"(?:^|(?<=[,)\]] ))" + r"\s*".join(re.escape(ch) for ch in name if not ch.isspace()), text, re.I)
        if found:
            m = re.match(r"(\s*[(\[][^()\[\]]*(?:[(\[][^()\[\]]*[)\]][^()\[\]]*)*[)\]])*", text[found.end():])
            text = text[:found.start()] + ", " + text[found.end() + m.end():]
    items = []
    for sentence in re.split(r"(?:(?<=[a-z]{3}\.)|(?<=\)\.))\s+(?=[A-Z])|;\s*", text):
        sentence = LIST_PREFIX_RE.sub("", sentence.strip().rstrip(".;").strip())
        if not sentence or ALLERGEN_SENTENCE_RE.match(sentence):
            continue
        parts = split_top_level(sentence)
        if parts:  # "... stearic acid (vegetable source) and silicon dioxide": split the last "and"
            last = parts.pop()
            parts += [p for p in re.split(r"\s+and\s+(?![^(\[]*[)\]])(?!mineral)", last) if p.strip()]
        for part in parts:
            part = LIST_PREFIX_RE.sub("", part.strip())
            split = bracket_list(part)
            if split and (EXCIPIENT_WRAPPER_RE.search(split[0]) or BLEND_WORD_RE.search(split[0])):
                items += [clean_verbatim(x) for x in split[1]]
            elif part:
                items.append(clean_verbatim(part))
    return [x for x in items if x and x.lower() != "none"]


def rows_from_raw_text(raw):
    """Labels with no rows: read the ingredient sentences from raw_text as x1, x2, ..."""
    m = re.search(r"Other ingredients\n(.+?)(?:\n\n|$)", raw, re.S)
    if not m:
        return []
    section = m.group(1)
    items = []  # (text, role)
    active = re.search(r"\| Purpose (.+?) \|", section)
    inactive = re.search(r"Inactive Ingredients:?\s*(.+?)\.?\s*$", section)
    if active or inactive:
        if active:
            items.append((active.group(1), "ingredient"))
        if inactive:
            items += [(x, "excipient") for x in split_top_level(inactive.group(1))]
    else:
        listing = re.split(r"\.\s{2,}|\.$", section.strip())[0]
        items = [(x, "excipient") for x in split_top_level(listing)]

    out = []
    for i, (text, role) in enumerate(items, 1):
        amt = AMOUNT_RE.search(text)
        name = text[:amt.start()] if amt else text
        value = float(amt.group(1).replace(",", "")) if amt else None
        if value is not None and value.is_integer():
            value = int(value)
        row = make_row(f"x{i}", text, name, role, None, value, amt.group(2) if amt else None)
        if role == "excipient":
            row["amount"]["scope"] = None
        out.append(row)
    return out


def public(row):
    """The row as schema.json defines it (internal hints removed)."""
    return {k: v for k, v in row.items() if not k.startswith("_")}
