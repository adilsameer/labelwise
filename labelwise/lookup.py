"""Part A, step 2: give each row one public id from a lookup.

Sources, all public:
  PubChem  name -> CID, UNII -> CID          (pubchem_cid)
  GSRS     exact name -> UNII                 (unii)
  NCBI     name -> taxonomy id, id -> name    (ncbi_taxid)

Every id comes from one of these answers; nothing is typed by hand.
"""
import re
import urllib.parse

from labelwise import rules
from labelwise.rows import COMPOUND_HEAD_RE
from labelwise.fetch import fetch_json

PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
GSRS = "https://gsrs.ncats.nih.gov/api/v1"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def identity(system, id_):
    url = {
        "pubchem_cid": f"https://pubchem.ncbi.nlm.nih.gov/compound/{id_}",
        "unii": f"https://gsrs.ncats.nih.gov/api/v1/substances({id_})",
        "ncbi_taxid": f"https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id={id_}",
    }[system]
    return {"system": system, "id": str(id_), "lookup_url": url}


# ---------------------------------------------------------------- sources

def pubchem_cids(name):
    _, j = fetch_json(f"{PUBCHEM}/compound/name/{urllib.parse.quote(name, safe='')}/cids/JSON")
    return j["IdentifierList"]["CID"] if j else []


def unii_cids(unii):
    _, j = fetch_json(f"{PUBCHEM}/substance/xref/RegistryID/{unii}/cids/JSON")
    if not j:
        return []
    return sorted({c for info in j["InformationList"]["Information"] for c in info.get("CID", [])})


def gsrs_exact(name):
    """Approved GSRS records that have this exact name."""
    phrase = name.upper().replace("\\", "\\\\").replace('"', '\\"')
    q = f'root_names_name:"^{phrase}$"'
    _, j = fetch_json(f"{GSRS}/substances/search?" + urllib.parse.urlencode({"q": q, "top": "10", "fdim": "0"}))
    hits = []
    for c in (j or {}).get("content", []):
        if c.get("approvalID") and not c.get("deprecated"):
            hits.append({"unii": c["approvalID"], "name": c.get("_name", ""), "record": c})
    return hits


def gsrs_organism(hit):
    """The organism a GSRS record is made from, as text, or None."""
    sd = hit["record"].get("structurallyDiverse") or {}
    if sd.get("organismGenus") and sd.get("organismSpecies"):
        name = f"{sd['organismGenus']} {sd['organismSpecies']}"
        rank = {"SUBSPECIES": "subsp.", "VARIETY": "var."}.get((sd.get("infraSpecificType") or "").upper())
        if rank and sd.get("infraSpecificName"):
            name += f" {rank} {sd['infraSpecificName'].lower()}"
        return name
    parent = (sd.get("parentSubstance") or {}).get("name") or (sd.get("parentSubstance") or {}).get("refPname")
    if parent:
        return re.sub(r"\s+(WHOLE|PLANT)$", "", parent, flags=re.I)
    return None


def ncbi_search(term):
    _, j = fetch_json(f"{EUTILS}/esearch.fcgi?" + urllib.parse.urlencode({"db": "taxonomy", "term": term, "retmode": "json"}))
    return j["esearchresult"]["idlist"] if j else []


def ncbi_names(ids):
    if not ids:
        return {}
    _, j = fetch_json(f"{EUTILS}/esummary.fcgi?" + urllib.parse.urlencode({"db": "taxonomy", "id": ",".join(ids), "retmode": "json"}))
    if not j:
        return {}
    return {i: (j["result"][i]["scientificname"], j["result"][i]["rank"]) for i in j["result"]["uids"]}


def ncbi_taxon(name):
    """(taxid, scientific name) when NCBI gives exactly one taxon for this name."""
    ids = ncbi_search(name)
    if len(ids) != 1:
        names = ncbi_names(ids)
        exact = [i for i, (n, _) in names.items() if n.lower() == name.lower()]
        if len(exact) != 1:
            return None
        ids = exact
    sci = ncbi_names(ids).get(ids[0], (None,))[0]
    return ids[0], sci


# ---------------------------------------------------------------- resolvers

def variants(name):
    out = [name]
    for pat, rep in rules.NAME_VARIANTS:
        v = re.sub(pat, rep, out[-1])
        if v != out[-1]:
            out.append(v)
    return out


LEADING_SYNONYMS = 10  # PubChem name search matches any synonym; we trust only the leading ones


def pubchem_synonyms(cid):
    _, j = fetch_json(f"{PUBCHEM}/compound/cid/{cid}/synonyms/JSON")
    return [s.lower() for s in j["InformationList"]["Information"][0].get("Synonym", [])] if j else []


def resolve_compound(name):
    """Return (identity, None) for one substance name, or (None, "code: why") / (None, None).

    GSRS (curated) comes first; its UNII is mapped to a CID through PubChem's own UNII xref.
    A PubChem-only match counts only when the name is a leading synonym of that compound
    ("kelp" is a deep synonym of astemizole, so it does not count).
    """
    weak = None
    for n in variants(name):
        hits = gsrs_exact(n)
        if len(hits) > 1:
            return None, f"ambiguous_name: GSRS has {len(hits)} substances named '{n}'"
        cids = pubchem_cids(n)
        if hits:
            unii = hits[0]["unii"]
            mapped = unii_cids(unii)
            if len(set(mapped) & set(cids)) == 1:
                return identity("pubchem_cid", (set(mapped) & set(cids)).pop()), None
            if len(mapped) == 1:
                return identity("pubchem_cid", mapped[0]), None
            return identity("unii", unii), None
        if len(cids) == 1:
            syns = pubchem_synonyms(cids[0])
            if n.lower() in syns[:LEADING_SYNONYMS]:
                return identity("pubchem_cid", cids[0]), None
            weak = weak or f"weak_synonym: PubChem matches '{n}' only as minor synonym of CID {cids[0]} ({syns[0] if syns else '?'}), GSRS has no such name"
        elif len(cids) > 1:
            weak = weak or f"ambiguous_name: PubChem has {len(cids)} compounds named '{n}' and GSRS has none"
    return None, weak


def singular(part):
    return rules.PART_SINGULAR.get(part, part)


def resolve_botanical(row):
    """GSRS exact names from most to least specific. Returns (identity, status, reason)."""
    latin, common = row["_latin"], row["_common"]
    bases = [b for b in (latin, common) if b]
    part = singular(row["_parts"][0]) if row["_parts"] else None
    phys = row["_physical"]
    levels = []  # (names, exact?)
    full = [" ".join(x for x in (b, part, phys) if x) for b in bases]
    levels.append((full, True))
    if part and phys:
        levels.append(([f"{b} {part}" for b in bases], False))
    if part or phys:
        levels.append((bases, False))

    for names, exact in levels:
        for n in dict.fromkeys(names):
            hits = gsrs_exact(n)
            if len(hits) > 1:
                return None, "review", f"ambiguous_name: GSRS has {len(hits)} substances named '{n}'"
            if not hits:
                continue
            hit = hits[0]
            clash = organism_clash(latin, hit) or organism_clash(common, hit, strict=False)
            if clash:
                return None, "review", f"ambiguous_name: {clash}"
            ident = identity("unii", hit["unii"])
            if exact:
                return ident, "identified", None
            what = " ".join(x for x in (part, phys) if x)
            return ident, "review", f"form_no_id: no UNII for the {what}; the id is for '{hit['name'].lower()}'"

    if latin:
        taxon = ncbi_taxon(latin)
        if taxon:
            return identity("ncbi_taxid", taxon[0]), "review", \
                f"form_no_id: no GSRS substance for this row; the id is for the plant {taxon[1]}"
    return None, "review", f"no_match: no GSRS name for {' / '.join(full)}"


def organism_clash(latin, hit, strict=True):
    """Explain when the GSRS record is made from a different organism than the label names.

    strict=False is for a common name ("turmeric"): it only clashes when NCBI knows the name.
    """
    if not latin:
        return None
    organism = gsrs_organism(hit)
    if not organism or organism.lower().startswith(latin.lower()):
        return None
    ours, theirs = ncbi_taxon(latin), ncbi_taxon(organism)
    if ours and theirs and ours[0] == theirs[0]:
        return None
    if not strict and not (ours and theirs):
        return None
    ours_txt = f"NCBI maps '{latin}' to {ours[1]} ({ours[0]})" if ours else f"NCBI has no single taxon for '{latin}'"
    return (f"GSRS gives '{hit['name'].lower()}' ({hit['unii']}) from {organism.lower()}, and {ours_txt}; "
            f"confirm which plant the label means")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def resolve_microbe(row):
    species = row["parent"]
    taxon = ncbi_taxon(species)
    via = ""
    if not taxon:  # old names NCBI does not know, e.g. Bifidobacterium infantis
        for hit in gsrs_exact(species)[:1]:
            org = gsrs_organism(hit) or hit["name"]
            taxon = ncbi_taxon(org)
            via = f" (label name found via GSRS {hit['unii']})"
    if not taxon:
        return None, "review", f"no_match: NCBI has no single taxon for '{species}'"
    taxid, sci = taxon
    strain = row["strain"]
    if not strain:
        return identity("ncbi_taxid", taxid), "identified", None

    for term in dict.fromkeys([f"{sci} {strain}", f"{species} {strain}"]):
        names = ncbi_names(ncbi_search(term))
        match = [i for i, (n, _) in names.items() if norm(strain) in norm(n) and n.lower().startswith(sci.lower().split(" subsp.")[0])]
        if len(match) == 1:
            return identity("ncbi_taxid", match[0]), "identified", None
    rank = ncbi_names([taxid]).get(taxid, (None, "species"))[1]
    return identity("ncbi_taxid", taxid), "review", \
        f"strain_no_id: no NCBI taxonomy id for strain {strain}; the id is for the {rank} {sci}{via}"


# ---------------------------------------------------------------- per row

def identify(row):
    """Fill identity, status and reason on a parsed row."""
    kind = row["_kind"]
    if kind in ("blend", "nutrition"):
        row.update(identity=None, status="review")
        return row
    if kind == "microbe":
        ident, status, reason = resolve_microbe(row)
        row.update(identity=ident, status=status, reason=reason)
        return row

    name = re.sub(r"\s+", " ", re.sub(r"[®™†‡*]", "", row["verbatim"])).strip(" .").lower()
    key = next((k for k in (name, row["parent"]) if k in rules.AMBIGUOUS_NAMES), None)
    if key:
        row.update(identity=None, status="review", reason=f"ambiguous_name: {rules.AMBIGUOUS_NAMES[key]}")
        return row
    if name in rules.NOT_ONE_SUBSTANCE or row["parent"] in rules.NOT_ONE_SUBSTANCE \
            or any(re.search(p, row["parent"] or "") for p in rules.NOT_ONE_SUBSTANCE_PATTERNS):
        row.update(identity=None, status="review", reason=f"not_one_substance: '{row['parent']}' names a class or mixture")
        return row

    if row["_multi_form"]:
        ident, _ = resolve_compound(row["parent"])
        row.update(identity=ident, status="review",
                   reason=f"multiple_forms: the row names several forms ({row['form']})")
        return row

    if row["form"] and row["form"] != row["_physical"]:  # a chemical form: the id must be for the form
        ident, why = resolve_compound(row["form"])
        if ident:
            row.update(identity=ident, status="identified", reason=None)
            return row
        nearest, _ = resolve_compound(row["parent"])
        row.update(identity=nearest, status="review",
                   reason=f"form_no_id: no id for the form '{row['form']}'" + (f"; the id is for '{row['parent']}'" if nearest else "")
                   + (f" ({why})" if why else ""))
        return row

    if row["_nutrient"]:
        nearest, _ = resolve_compound(row["parent"])
        row.update(identity=nearest, status="review",
                   reason=f"form_not_given: the label does not say which form of {row['parent']}"
                   + ("; the id is for the nutrient name" if nearest else ""))
        return row

    compound = COMPOUND_HEAD_RE.search(row["parent"] or "")  # "Berberine HCl (from barberry root)"
    if not compound and (row["_latin"] or row["_parts"]) or not compound and row["_physical"] in ("extract", "extract powder", "powder", "juice concentrate", "concentrate"):
        # a substance name that PubChem or GSRS knows as a whole (e.g. "eucalyptus oil") wins first
        if not row["_latin"] and not row["_parts"]:
            ident, _ = resolve_compound(" ".join(x for x in (row["parent"], row["_physical"]) if x))
            if ident:
                row.update(identity=ident, status="identified", reason=None)
                return row
        ident, status, reason = resolve_botanical(row)
        row.update(identity=ident, status=status, reason=reason)
        return row

    why = None
    phys = row["_physical"]
    names = [f"{row['parent']} {phys}"] if phys and phys not in row["parent"] else []
    names += [n for n in row["_names"] if n != phys]
    for n in dict.fromkeys(names):
        ident, note = resolve_compound(n)
        if ident:
            row.update(identity=ident, status="identified", reason=None)
            return row
        why = why or note
    row.update(identity=None, status="review",
               reason=why if why else f"no_match: no PubChem or GSRS name '{row['parent']}'")
    return row
