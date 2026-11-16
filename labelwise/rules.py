"""Hand-written rules. Names and spelling only: no ids live here (rule 1)."""

# Names that can mean more than one substance. Checked before any lookup.
# key: the row name in lower case; value: the detail for the review reason.
AMBIGUOUS_NAMES = {
    "vegetable cellulose": "'vegetable cellulose' can mean cellulose or hypromellose (a capsule shell)",
    "vegetable stearate": "'vegetable stearate' can mean magnesium stearate or stearic acid",
    "vegetable magnesium stearate": "'vegetable magnesium stearate' does not say which fatty acid salt mix",
    "vegetable capsule": "'vegetable capsule' does not name the capsule material",
    "veggie capsule": "'veggie capsule' does not name the capsule material",
    "capsule": "'capsule' does not name the capsule material",
    "softgel": "'softgel' does not name the shell material",
    "cellulose": "'cellulose' does not say which cellulose (GSRS has powdered and microcrystalline, no plain 'cellulose')",
}

# Names that are a class or a mixture, not one substance.
NOT_ONE_SUBSTANCE = {
    "natural flavor", "natural flavors", "natural flavour", "flavor", "flavors", "natural flavoring",
    "artificial flavor", "artificial flavors", "colors", "color", "natural colors", "natural color",
    "fruit and vegetable juice", "vegetable juice", "fragrance", "parfum", "proteins", "enzymes",
    "other omega-3 fatty acids", "omega-3 fatty acids", "fatty acids", "polyphenols", "tocopherols",
    "mixed tocopherols", "fiber", "epa/dha", "polysaccharides", "emulsifier", "anti-caking agent", "lipid",
    "ingredients", "enteric coating", "prebiotic fiber", "algae", "nothing else",
}

# The same as NOT_ONE_SUBSTANCE, as patterns: "cherry flavor", "total omega-3s", "other ...".
NOT_ONE_SUBSTANCE_PATTERNS = [r"\bflavou?rs?$", r"\bflavou?ring$", r"^total ", r"^other ", r"^typical "]

# Spelling variants tried after the name as written. (pattern, replacement)
NAME_VARIANTS = [
    (r"\bhcl\b", "hydrochloride"),
    (r"\bthiamin\b", "thiamine"),
    (r"\bvitamin b-(\d+)", r"vitamin b\1"),
    (r"\bvitamin d-(\d)", r"vitamin d\1"),
    (r"^(dl?)-alpha[ -]", r"\1-alpha-"),
    (r"tocopheryl succinate$", "tocopherol succinate"),
    (r"\bl-5-methylfolate\b", "levomefolic acid"),
    (r"\bl-5-methyltetrahydrofolate\b", "levomefolic acid"),
    (r"\bbisglycinate\b", "glycinate"),
    (r"\s+chelate$", ""),
    (r"^hpmc$", "hypromellose"),
    (r"^medium chain triglyceride( oil)?s?$", "medium chain triglycerides"),
    (r"#\s*(\d+)", r"no. \1"),
]

# Ingredient trademarks that sit in front of a chemical form ("Albion Zinc Bisglycinate").
BRAND_WORDS = {"albion", "traacs", "ferrochel", "aquamin", "chelamax", "kelatron", "optizinc",
               "chromax", "quatrefolic", "metafolin", "sunactive"}

# Plural plant parts -> the singular GSRS uses.
PART_SINGULAR = {"roots": "root", "leaves": "leaf", "seeds": "seed", "berries": "berry",
                 "flowers": "flower", "fruiting bodies": "fruiting body"}
