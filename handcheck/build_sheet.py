"""Build handcheck/review.html: the 20 sample labels, the program output and the pre-marks.

python handcheck/build_sheet.py
Open review.html in a browser, confirm or change every mark, then "Export marks.json"
and run: python handcheck/score.py handcheck/marks.json
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERE = ROOT / "handcheck"


def blank_marks(out):
    return {
        "label_id": out["label_id"],
        "rows": [{"row_id": r["row_id"], "parse": "ok", "identity": "ok", "note": ""} for r in out["rows"]],
        "missed_rows": [],
        "claims": [{"claim_id": c["claim_id"], "mark": "ok", "note": ""} for c in out["claims"]],
        "missed_claims": [],
        "candidates": [{"n": i, "mark": "ok", "note": ""} for i, _ in enumerate(out["candidates"], 1)],
        "evidence": [{"row_id": e["row_id"], "mark": "ok", "note": ""} for e in out["evidence"]],
    }


def merge(pre, base, out):
    """Keep a pre-mark only where the output is unchanged since the pre-check; flag everything else."""
    m = blank_marks(out)
    for part in ("rows", "claims", "candidates", "evidence"):
        for x in m[part]:
            for k in ("parse", "identity", "mark"):
                if k in x:
                    x[k] = None
            x["changed"] = True
    base_rows = {r["row_id"]: r for r in base["rows"]}
    pre_rows = {r["row_id"]: r for r in pre["rows"]}
    for x, r in zip(m["rows"], out["rows"]):
        old = pre_rows.get(r["row_id"])
        if old and base_rows.get(r["row_id"]) == r:
            x.update(parse=old["parse"], identity=old["identity"], note=old.get("note", ""), changed=False)
        elif old and old.get("note"):
            x["pre_note"] = old["note"]
    base_claims = {c["claim_id"]: c for c in base["claims"]}
    pre_claims = {c["claim_id"]: c for c in pre["claims"]}
    for x, c in zip(m["claims"], out["claims"]):
        if base_claims.get(c["claim_id"]) == c and c["claim_id"] in pre_claims:
            old = pre_claims[c["claim_id"]]
            x.update(mark=old["mark"], note=old.get("note", ""), changed=False)
    base_cands = {(c["phrase"], c["quote"]): i for i, c in enumerate(base["candidates"], 1)}
    pre_cands = {c["n"]: c for c in pre["candidates"]}
    for x, c in zip(m["candidates"], out["candidates"]):
        old = pre_cands.get(base_cands.get((c["phrase"], c["quote"])))
        if old:
            x.update(mark=old["mark"], note=old.get("note", ""), changed=False)
    base_ev = {e["row_id"]: e for e in base["evidence"]}
    pre_ev = {e["row_id"]: e for e in pre["evidence"]}
    for x, e in zip(m["evidence"], out["evidence"]):
        if base_ev.get(e["row_id"]) == e and e["row_id"] in pre_ev:
            old = pre_ev[e["row_id"]]
            x.update(mark=old["mark"], note=old.get("note", ""), changed=False)
    found = {c["claim_id"] for c in out["claims"]}
    m["missed_claims"] = [c for c in pre.get("missed_claims", []) if c["claim_id"] not in found]
    verbatims = " | ".join(r["verbatim"].lower() for r in out["rows"])
    m["missed_rows"] = [r for r in pre.get("missed_rows", []) if r["text"].lower()[:20] not in verbatims]
    return m


def main():
    sample = json.loads((HERE / "sample.json").read_text())["labels"]
    labels = {}
    for line in open(ROOT / "labels.jsonl", encoding="utf-8"):
        if line.strip():
            lab = json.loads(line)
            labels[lab["label_id"]] = lab
    data = []
    for lid in sample:
        name = lid.replace(":", "_") + ".json"
        out = json.loads((ROOT / "output" / name).read_text())
        pre, base = HERE / "premarks" / name, HERE / "premarks_base" / name
        if pre.exists() and base.exists():
            marks = merge(json.loads(pre.read_text()), json.loads(base.read_text()), out)
        else:
            marks = blank_marks(out)
        lab = labels[lid]
        data.append({"label": {k: lab.get(k) for k in ("label_id", "source_url", "title", "brand", "raw_text")},
                     "out": out, "marks": marks, "premarked": pre.exists()})
    html = TEMPLATE.replace("/*DATA*/", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    (HERE / "review.html").write_text(html)
    todo = sum(x.get("changed", False) for d in data for part in ("rows", "claims", "candidates", "evidence")
               for x in d["marks"][part])
    print(f"wrote handcheck/review.html ({len(data)} labels, {sum(d['premarked'] for d in data)} pre-marked, "
          f"{todo} items changed since the pre-check and left unmarked)")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hand Check Sheet</title>
<style>
:root {
  --bg: #f7f7f5; --panel: #ffffff; --text: #1d1d1b; --muted: #6b6b66; --line: #e2e1dc;
  --ok: #1f7a4d; --ok-bg: #e6f4ec; --bad: #b42318; --bad-bg: #fdecea; --accent: #2f5bd3; --code: #f1f0ec;
  --todo-bg: #fff6d6;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #161615; --panel: #1f1f1d; --text: #ecebe6; --muted: #a09f98; --line: #34332f;
    --ok: #5fcf95; --ok-bg: #173527; --bad: #ff8a7e; --bad-bg: #3d1d1a; --accent: #8aa8ff; --code: #2a2a27;
    --todo-bg: #3a3215;
  }
}
:root[data-theme="dark"] {
  --bg: #161615; --panel: #1f1f1d; --text: #ecebe6; --muted: #a09f98; --line: #34332f;
  --ok: #5fcf95; --ok-bg: #173527; --bad: #ff8a7e; --bad-bg: #3d1d1a; --accent: #8aa8ff; --code: #2a2a27;
  --todo-bg: #3a3215;
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text); font: 14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
header { position: sticky; top: 0; z-index: 5; background: var(--panel); border-bottom: 1px solid var(--line);
  padding: 10px 16px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
header h1 { font-size: 16px; margin: 0 12px 0 0; }
header .stat { color: var(--muted); }
header .stat b { color: var(--text); }
button { font: inherit; border: 1px solid var(--line); background: var(--panel); color: var(--text);
  border-radius: 6px; padding: 5px 10px; cursor: pointer; }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
main { max-width: 1200px; margin: 0 auto; padding: 16px; }
nav { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 16px; }
nav a { text-decoration: none; color: var(--text); background: var(--panel); border: 1px solid var(--line);
  border-radius: 999px; padding: 2px 10px; font-size: 12px; }
nav a.has-wrong { border-color: var(--bad); color: var(--bad); }
section.label { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px; margin-bottom: 20px; }
section.label h2 { font-size: 15px; margin: 0 0 4px; }
.meta { color: var(--muted); font-size: 12px; margin-bottom: 8px; word-break: break-word; }
.meta a { color: var(--accent); }
details pre { white-space: pre-wrap; background: var(--code); padding: 10px; border-radius: 6px; font-size: 12px; max-height: 360px; overflow: auto; }
h3 { font-size: 13px; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); margin: 16px 0 6px; }
.table { width: 100%; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 12.5px; }
th, td { text-align: left; vertical-align: top; padding: 6px; border-top: 1px solid var(--line); }
th { color: var(--muted); font-weight: 600; }
tr.wrong td { background: var(--bad-bg); }
tr.todo td { background: var(--todo-bg); }
.prenote { color: var(--muted); font-size: 11px; font-style: italic; }
code { background: var(--code); padding: 0 4px; border-radius: 4px; font-size: 12px; }
.small { color: var(--muted); font-size: 11.5px; }
.toggle { display: inline-flex; border: 1px solid var(--line); border-radius: 6px; overflow: hidden; }
.toggle button { border: 0; border-radius: 0; padding: 3px 8px; font-size: 12px; }
.toggle button.on.ok { background: var(--ok-bg); color: var(--ok); font-weight: 600; }
.toggle button.on.wrong { background: var(--bad-bg); color: var(--bad); font-weight: 600; }
input.note { width: 100%; min-width: 160px; font: inherit; font-size: 12px; padding: 3px 6px; border: 1px solid var(--line);
  border-radius: 4px; background: var(--panel); color: var(--text); margin-top: 4px; }
.missed { display: flex; gap: 6px; margin: 4px 0; flex-wrap: wrap; }
.missed input { flex: 1; min-width: 120px; }
@media (max-width: 700px) { th.hide-sm, td.hide-sm { display: none; } }
</style>
</head>
<body>
<header>
  <h1>Hand check · 20 labels</h1>
  <span class="stat">to check: <b id="ntodo">0</b></span>
  <span class="stat">wrong marks: <b id="nwrong">0</b></span>
  <span class="stat">pre-marked by AI reviewers; confirm or change each mark</span>
  <span style="flex:1"></span>
  <button id="reset">Reset to pre-marks</button>
  <button class="primary" id="export">Export marks.json</button>
</header>
<main>
  <nav id="nav"></nav>
  <div id="labels"></div>
</main>
<script>
const DATA = /*DATA*/;
const KEY = "handcheck-marks-v2";
let marks = DATA.map(d => JSON.parse(JSON.stringify(d.marks)));
try { const saved = JSON.parse(localStorage.getItem(KEY) || "null"); if (saved && saved.length === marks.length) marks = saved; } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(marks)); } catch (e) {} update(); };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const find = (list, key, val) => list.find(x => String(x[key]) === String(val));

function toggle(obj, field, onchange) {
  const wrap = document.createElement("span"); wrap.className = "toggle";
  for (const v of ["ok", "wrong"]) {
    const b = document.createElement("button"); b.textContent = v; b.className = v + (obj[field] === v ? " on" : "");
    b.onclick = () => { obj[field] = v; obj.changed = false; onchange(); };
    wrap.appendChild(b);
  }
  return wrap;
}
function noteInput(obj) {
  const i = document.createElement("input"); i.className = "note"; i.placeholder = "note (required when wrong)";
  i.value = obj.note || ""; i.oninput = () => { obj.note = i.value; save(); };
  return i;
}
function ident(r) {
  if (!r.identity) return '<span class="small">no id</span>';
  return `<a href="${esc(r.identity.lookup_url)}" target="_blank" rel="noopener">${esc(r.identity.system)} ${esc(r.identity.id)}</a>`;
}
function fields(r) {
  const parts = [["parent", r.parent], ["form", r.form], ["source", r.source], ["strain", r.strain], ["std", r.standardization],
    ["role", r.role], ["group", r.group], ["amount", r.amount.value != null ? `${r.amount.value} ${r.amount.unit ?? ""}` : null],
    ["scope", r.amount.scope], ["blend", r.blend_contents]];
  return parts.filter(p => p[1] != null).map(p => `<span class="small">${p[0]}</span> ${esc(p[1])}`).join(" · ");
}

function render() {
  const root = document.getElementById("labels"); root.innerHTML = "";
  const nav = document.getElementById("nav"); nav.innerHTML = "";
  DATA.forEach((d, li) => {
    const m = marks[li], out = d.out, lab = d.label;
    const a = document.createElement("a"); a.href = "#L" + li; a.textContent = lab.label_id; nav.appendChild(a);
    const sec = document.createElement("section"); sec.className = "label"; sec.id = "L" + li;
    sec.innerHTML = `<h2>${esc(lab.label_id)} · ${esc(lab.title)}</h2>
      <div class="meta">${esc(lab.brand)} · <a href="${esc(lab.source_url)}" target="_blank" rel="noopener">source page</a>
      ${d.premarked ? "" : " · <b>not pre-marked</b>"}</div>
      <details><summary>raw_text</summary><pre>${esc(lab.raw_text)}</pre></details>`;
    const rerender = () => { save(); render(); location.hash = "#L" + li; };

    // rows
    sec.insertAdjacentHTML("beforeend", "<h3>A · rows</h3>");
    const rt = document.createElement("div"); rt.className = "table";
    rt.innerHTML = '<table><thead><tr><th>row</th><th>verbatim</th><th class="hide-sm">parsed</th><th>id / status</th><th>parse</th><th>identity</th></tr></thead><tbody></tbody></table>';
    out.rows.forEach(r => {
      const mk = find(m.rows, "row_id", r.row_id) || (m.rows.push({row_id: r.row_id, parse: "ok", identity: "ok", note: ""}), m.rows.at(-1));
      const tr = document.createElement("tr");
      tr.className = (mk.parse == null || mk.identity == null) ? "todo" : (mk.parse === "wrong" || mk.identity === "wrong") ? "wrong" : "";
      tr.innerHTML = `<td><code>${esc(r.row_id)}</code></td><td>${esc(r.verbatim)}</td><td class="hide-sm">${fields(r)}</td>
        <td>${ident(r)}<br><span class="small">${esc(r.status)}${r.reason ? ": " + esc(r.reason) : ""}</span></td><td></td><td></td>`;
      tr.children[4].appendChild(toggle(mk, "parse", rerender));
      tr.children[5].appendChild(toggle(mk, "identity", rerender));
      tr.children[5].appendChild(noteInput(mk));
      if (mk.pre_note) tr.children[5].insertAdjacentHTML("beforeend", `<div class="prenote">pre-check (old output): ${esc(mk.pre_note)}</div>`);
      rt.querySelector("tbody").appendChild(tr);
    });
    sec.appendChild(rt);
    sec.appendChild(missedList(m, "missed_rows", ["text", "note"], "+ missed row", rerender));

    // claims
    sec.insertAdjacentHTML("beforeend", "<h3>B · claims</h3>");
    sec.appendChild(simpleTable(out.claims, c => find(m.claims, "claim_id", c.claim_id),
      c => `<code>${esc(c.claim_id)}</code> ${esc(c.claim)}`, c => `“${esc(c.quote)}” <span class="small">(${esc(c.where)})</span>`, rerender));
    sec.appendChild(missedList(m, "missed_claims", ["claim_id", "quote", "note"], "+ missed claim", rerender));

    sec.insertAdjacentHTML("beforeend", "<h3>B · candidates</h3>");
    sec.appendChild(simpleTable(out.candidates.map((c, i) => ({...c, n: i + 1})), c => find(m.candidates, "n", c.n),
      c => esc(c.phrase), c => `“${esc(c.quote)}”`, rerender));
    if (out.for_a_person.length) {
      sec.insertAdjacentHTML("beforeend", "<h3>B · for a person</h3>" + out.for_a_person.map(p =>
        `<div class="small"><b>${esc(p.kind)}</b>: ${esc(p.note)} — “${esc(p.quote)}”</div>`).join(""));
    }

    // evidence
    sec.insertAdjacentHTML("beforeend", "<h3>C · evidence</h3>");
    sec.appendChild(simpleTable(out.evidence, e => find(m.evidence, "row_id", e.row_id),
      e => `<code>${esc(e.row_id)}</code> ${esc(e.status)}`,
      e => `${esc(e.summary || "no_record")}<br><a class="small" href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.url)}</a>`, rerender));
    root.appendChild(sec);
    if (JSON.stringify(m).includes('"wrong"') || (m.missed_rows || []).length || (m.missed_claims || []).length) a.className = "has-wrong";
  });
  update();
}
function simpleTable(items, getMark, c1, c2, rerender) {
  const wrap = document.createElement("div"); wrap.className = "table";
  if (!items.length) { wrap.innerHTML = '<div class="small">none</div>'; return wrap; }
  wrap.innerHTML = "<table><tbody></tbody></table>";
  items.forEach(it => {
    const mk = getMark(it) || {mark: null, note: ""};
    const tr = document.createElement("tr"); tr.className = mk.mark == null ? "todo" : mk.mark === "wrong" ? "wrong" : "";
    tr.innerHTML = `<td style="width:28%">${c1(it)}</td><td>${c2(it)}</td><td style="width:220px"></td>`;
    tr.children[2].appendChild(toggle(mk, "mark", rerender));
    tr.children[2].appendChild(noteInput(mk));
    wrap.querySelector("tbody").appendChild(tr);
  });
  return wrap;
}
function missedList(m, key, cols, label, rerender) {
  m[key] = m[key] || [];
  const box = document.createElement("div");
  m[key].forEach((item, i) => {
    const row = document.createElement("div"); row.className = "missed";
    cols.forEach(c => { const inp = document.createElement("input"); inp.className = "note"; inp.placeholder = c; inp.value = item[c] || "";
      inp.oninput = () => { item[c] = inp.value; save(); }; row.appendChild(inp); });
    const del = document.createElement("button"); del.textContent = "remove"; del.onclick = () => { m[key].splice(i, 1); rerender(); };
    row.appendChild(del); box.appendChild(row);
  });
  const add = document.createElement("button"); add.textContent = label; add.style.marginTop = "6px";
  add.onclick = () => { m[key].push(Object.fromEntries(cols.map(c => [c, ""]))); rerender(); };
  box.appendChild(add);
  return box;
}
function update() {
  const n = JSON.stringify(marks).split('"wrong"').length - 1 + marks.reduce((s, m) => s + (m.missed_rows || []).length + (m.missed_claims || []).length, 0);
  document.getElementById("nwrong").textContent = n;
  const todo = marks.reduce((s, m) => s + ["rows", "claims", "candidates", "evidence"].reduce((t, p) =>
    t + (m[p] || []).filter(x => x.mark === null || x.parse === null || x.identity === null).length, 0), 0);
  document.getElementById("ntodo").textContent = todo;
}
document.getElementById("export").onclick = () => {
  const blob = new Blob([JSON.stringify(marks, null, 2)], {type: "application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "marks.json"; a.click();
};
document.getElementById("reset").onclick = () => {
  marks = DATA.map(d => JSON.parse(JSON.stringify(d.marks)));
  try { localStorage.removeItem(KEY); } catch (e) {}
  render();
};
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
