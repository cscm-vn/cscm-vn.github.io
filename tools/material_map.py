"""Map hub price items / contract items onto data/registry/material_taxonomy.json (master-data tree).
Rules live in data/registry/material_taxonomy_rules.json (first match wins, regex on unaccented lowercase
'category | id | name'). Output: data/registry/material_taxonomy_map.json (+ site/data/mt.json via trends/build.py).
Confidence: high = master data names the same material; medium = material is the main input of that price family
(master-data wording/remark supports it); low = best-effort nearest family, needs team confirmation.
Items with no master-data family (world commodities, FX, gold) are NOT forced: listed as unmapped with optional
'related' families they drive (e.g. LME copper → Cáp điện)."""
import json, os, re, unicodedata as U, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "data", "registry")
def strip(s):
    return "".join(c for c in U.normalize("NFD", s or "") if U.category(c) != "Mn").replace("đ", "d").replace("Đ", "D").lower()
def load():
    tax = json.load(open(os.path.join(REG, "material_taxonomy.json"), encoding="utf-8"))
    rules = json.load(open(os.path.join(REG, "material_taxonomy_rules.json"), encoding="utf-8"))
    return tax, rules
def path_of(code, by):
    p = []
    while code: n = by[code]; p.insert(0, n); code = n["parent"]
    return p
def match(text, rules, by):
    for r in rules:
        if re.search(r["re"], text):
            if r.get("code"):
                assert r["code"] in by, r["code"]
                return dict(code=r["code"], conf=r["conf"], why=r["why"])
            return dict(code=None, conf="none", why=r["why"], related=r.get("related", []))
    return dict(code=None, conf="none", why="Không khớp quy tắc nào – cần nhóm xác nhận")
def map_text(text, kind="items"):
    """Map a free-text label (e.g. a forecast series 'group | key | name') with the same rules."""
    tax, rules = load(); by = {n["code"]: n for n in tax["nodes"]}
    d = match(strip(text), rules[kind], by)
    if d["code"]: d["path"] = [n["name_vi"] for n in path_of(d["code"], by)]
    return d
def build(write=True):
    tax, rules = load(); by = {n["code"]: n for n in tax["nodes"]}
    items = json.load(open(os.path.join(REG, "items.json"), encoding="utf-8"))
    out_items = {}
    for it in items:
        m = it.get("meta", {}); txt = strip(f"{m.get('category','')} | {it['id']} | {m.get('name','')}")
        out_items[it["id"]] = match(txt, rules["items"], by)
    cb = json.load(open(os.path.join(REG, "contract_baselines.json"), encoding="utf-8"))
    out_c = {}
    for c in cb["contracts"]:
        for i in c["items"]:
            txt = strip(f"{i.get('group','')} | {i['code']} | {i.get('desc','')}")
            out_c[i["code"]] = match(txt, rules["contract"], by) | {"desc": i.get("desc")}
    for d in list(out_items.values()) + list(out_c.values()):
        if d["code"]: d["path"] = [n["name_vi"] for n in path_of(d["code"], by)]
        if d.get("related"): d["related_path"] = [" › ".join(n["name_vi"] for n in path_of(c, by)) for c in d["related"]]
    res = dict(schema_version=1,
               taxonomy="material_taxonomy.json", rules="material_taxonomy_rules.json",
               summary=dict(items=len(out_items), mapped=sum(1 for d in out_items.values() if d["code"]),
                            by_conf={k: sum(1 for d in out_items.values() if d["conf"] == k) for k in ("high", "medium", "low", "none")},
                            contract=len(out_c), contract_mapped=sum(1 for d in out_c.values() if d["code"])),
               unmapped=sorted(k for k, d in out_items.items() if not d["code"]), items=out_items, contract_items=out_c)
    if write:
        json.dump(res, open(os.path.join(REG, "material_taxonomy_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return tax, res
if __name__ == "__main__":
    _, r = build(); print(json.dumps(r["summary"], ensure_ascii=False)); print("unmapped:", r["unmapped"])
