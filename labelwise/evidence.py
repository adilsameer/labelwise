"""Part C: for each identified row, the PubChem GHS classification record.

no_record means only that PubChem has no GHS record for this id. It never means safe.
"""
import json
import re

from labelwise.fetch import fetch

PUG = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
PUG_VIEW = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view"
SOURCE = "pubchem_ghs"
SOURCE_LABEL = {"European Chemicals Agency (ECHA)": "ECHA C&L via PubChem"}


def ghs_summary(body):
    """Short text of what the GHS record says, or None when the response has no GHS section."""
    try:
        record = json.loads(body)["Record"]
    except (ValueError, KeyError, TypeError):
        return None
    refs = {r["ReferenceNumber"]: (r.get("SourceName", "?"), r.get("Name")) for r in record.get("Reference", [])}

    infos = []
    def walk(section):
        for s in section.get("Section", []):
            if s.get("TOCHeading") == "GHS Classification":
                infos.extend(s.get("Information", []))
            walk(s)
    walk(record)
    if not infos:
        return None

    parts = {}  # reference number -> {"codes": [...], "not_classified": text}; one per notification
    for info in infos:
        part = parts.setdefault(info.get("ReferenceNumber"), {"codes": [], "not_classified": None})
        texts = [v.get("String", "") for v in info.get("Value", {}).get("StringWithMarkup", [])]
        if info.get("Name") == "GHS Hazard Statements":
            for t in texts:
                m = re.match(r"(H\d{3}[A-Za-z]*(?:\+H\d{3}[A-Za-z]*)*)(?:\s*\((\d+(?:\.\d+)?)%\))?", t)
                if m:
                    code = m.group(1) + (f" ({m.group(2)}%)" if m.group(2) else "")
                    if code not in part["codes"]:
                        part["codes"].append(code)
                elif re.search(r"not classified", t, re.I):
                    part["not_classified"] = part["not_classified"] or "Not Classified"
        elif info.get("Name") in ("Note", "ECHA C&L Notifications Summary"):
            for t in texts:
                m = re.search(r"does not meet GHS hazard criteria for [\d.]+% \((\d+) of (\d+)\)", t) or \
                    re.search(r"not meeting GHS hazard criteria per (\d+) of (\d+) reports", t)
                if m:
                    part["not_classified"] = f"{m.group(1)} of {m.group(2)} reports Not Classified"

    by_source = {}  # source label -> [(entry name, text)]
    for ref, part in parts.items():
        if not part["codes"] and not part["not_classified"]:
            continue
        text = ", ".join(part["codes"])
        if part["not_classified"]:
            text = f"{text}; {part['not_classified']}" if text else part["not_classified"]
        source, name = refs.get(ref, ("?", None))
        by_source.setdefault(SOURCE_LABEL.get(source, source), []).append((name, text))

    out = []
    for source, entries in by_source.items():
        if len(entries) == 1:
            out.append(f"{source}: {entries[0][1]}.")
        else:
            out.append(f"{source}, {len(entries)} entries: " + "; ".join(f"{n}: {t}" for n, t in entries) + ".")
    return " ".join(out) or "GHS Classification section present with no hazard statements."


def cid_evidence(cid):
    url = f"{PUG_VIEW}/data/compound/{cid}/JSON?heading=GHS+Classification"
    entry = fetch(url)
    summary = ghs_summary(entry["body"]) if entry["status"] == 200 else None
    return url, entry, summary, f"evidence/{SOURCE}/{cid}.json"


def evidence_for(ident):
    """Return (item fields, copy_path, cached entry) for one identity."""
    system, id_ = ident["system"], ident["id"]
    if system == "pubchem_cid":
        url, entry, summary, path = cid_evidence(id_)
    elif system == "unii":
        url = f"{PUG}/substance/xref/RegistryID/{id_}/cids/JSON"
        entry = fetch(url)
        cids = []
        if entry["status"] == 200:
            info = json.loads(entry["body"])["InformationList"]["Information"]
            cids = sorted({c for i in info for c in i.get("CID", [])})
        summary, path = None, f"evidence/{SOURCE}/unii_{id_}.json"
        if len(cids) == 1:  # the UNII has one PubChem compound: its GHS record is the evidence
            url, entry, summary, path = cid_evidence(cids[0])
    else:  # ncbi_taxid: PubChem keeps organisms as taxonomy pages, which have no GHS section
        url = f"{PUG_VIEW}/data/taxonomy/{id_}/JSON"
        entry = fetch(url)
        summary, path = None, f"evidence/{SOURCE}/taxid_{id_}.json"
    item = {
        "source": SOURCE,
        "status": "record" if summary else "no_record",
        "summary": summary,
        "date": entry["date"],
        "url": url,
        "copy_path": path,
    }
    return item, path, entry


def build_evidence(rows):
    """Evidence items for the identified rows, and the copies to store {copy_path: entry}."""
    items, copies = [], {}
    for row in rows:
        if row["status"] != "identified":
            continue
        item, path, entry = evidence_for(row["identity"])
        items.append({"row_id": row["row_id"], **item})
        copies[path] = entry
    return items, copies
