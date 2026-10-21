#!/usr/bin/env python3
"""Turn ./site (built by export_static.py) into the daily hub. Run AFTER export_static.py (and after any forecast build).
- moves the price table to site/gia.html (keeps it working) and injects the shared nav,
- copies hub pages from trends/web/ and data (taxonomy, trends, market, feed) to site/data/,
- computes site/data/hub.json: every price item mapped to the taxonomy, MoM/YoY, monthly series,
  Hà Nội vs TP.HCM comparisons with insight text, monthly digest."""
import json, os, re, shutil, glob, unicodedata, datetime as dt
from statistics import mean
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); SITE = os.path.join(ROOT, "site"); OUT = os.path.join(SITE, "data")
TZ = dt.timezone(dt.timedelta(hours=7))
def strip(s):
    s = unicodedata.normalize("NFD", (s or "").lower()); return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
def J(p, default=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return default
TAXF = os.path.join(ROOT, "data", "taxonomy.json") if os.path.exists(os.path.join(ROOT, "data", "taxonomy.json")) else os.path.join(H, "data", "taxonomy.json")
TAX = J(TAXF); L2 = [(n, c) for n in TAX["tree"] for c in n["children"]]
def classify(it):
    name, cat, iid = strip(it.get("name")), it.get("category"), it.get("id", "")
    for n, c in L2:
        if cat in c.get("match", {}).get("cats", []): return c["id"]
    for n, c in L2:
        if any(k in iid for k in c.get("match", {}).get("ids", [])): return c["id"]
    for n, c in L2:
        if any(strip(k) in name for k in c.get("match", {}).get("kw", [])): return c["id"]
    return "tt.ty-gia" if it.get("grp") == "world" else "xd.cat-da"
def region(it):
    r = it.get("region") or ""
    for k, names in TAX["regions"].items():
        if r in names: return k
    return "vn" if it.get("grp") == "vn" else "world"
def pt_at(points, days):
    """price ~days before the last point (closest point within 40% tolerance)."""
    if len(points) < 2: return None
    last = dt.date.fromisoformat(points[-1]["date"]); target = last - dt.timedelta(days=days)
    best = min(points[:-1], key=lambda p: abs((dt.date.fromisoformat(p["date"]) - target).days))
    return best if abs((dt.date.fromisoformat(best["date"]) - target).days) <= days * 0.4 else None
def pct(a, b): return round((a / b - 1) * 100, 2) if a is not None and b else None
def mid(it): return (it["price"] + it["price_high"]) / 2 if it.get("price_high") else it.get("price")
PAIRS = [  # label, HN regex, HCM regex (on accent-free name), tax, note
 ("Thép CB240 D6 cuộn (TB các hãng)", r"cb240 d6", r"cb240 d6", "xd.cot-thep", "steel"),
 ("Thép CB300 D10 (TB các hãng)", r"cb300 d10", r"cb300 d10", "xd.cot-thep", "steel"),
 ("Thép CB400 D16 (TB các hãng)", r"cb400 d16", r"cb400 d16", "xd.cot-thep", "steel"),
 ("Thép CB500 D16 (TB các hãng)", r"cb500 d16", r"cb500 d16", "xd.cot-thep", "steel"),
 ("Xi măng PCB40 bao", r"bao pcb40|new elephant pcb40", r"^xi mang pcb40 bao$", "xd.xi-mang", "sxd"),
 ("Xi măng PCB40 rời", r"roi pcb40", r"^xi mang pcb40 roi$", "xd.xi-mang", "sxd"),
 ("Đá 1x2", r"^da 1x2", r"^da 1x2", "xd.cat-da", "sxd"),
 ("Đá 4x6", r"^da 4x6", r"^da 4x6", "xd.cat-da", "sxd"),
 ("Cấp phối đá dăm", r"cap phoi", r"cap phoi", "xd.cat-da", "sxd"),
 ("Cát vàng (HN) / cát bê tông (HCM)", r"^cat vang", r"^cat be tong", "xd.cat-da", "sxd"),
 ("Cát san nền / san lấp", r"cat san", r"cat san", "xd.cat-da", "sxd"),
 ("Bê tông tươi M250 đá 1x2", r"m250", r"m250", "xd.be-tong", "rmc"),
 ("Bê tông tươi M300 đá 1x2", r"m300", r"m300", "xd.be-tong", "rmc"),
 ("Bê tông tươi M350 đá 1x2", r"m350", r"m350", "xd.be-tong", "rmc"),
 ("Bê tông tươi M400 đá 1x2", r"m400", r"m400", "xd.be-tong", "rmc"),
 ("Bê tông tươi M450 đá 1x2", r"m450", r"m450", "xd.be-tong", "rmc"),
 ("Bê tông tươi M500 đá 1x2", r"m500", r"m500", "xd.be-tong", "rmc"),
]
def vn(v, d=0):
    """Vietnamese number format: 1.234.567 / 12,5"""
    s = f"{v:,.{d}f}"; return s.replace(",", "§").replace(".", ",").replace("§", ".")
HINT = {"xd.be-tong": "Bê tông tươi phụ thuộc giá xi măng, cát, đá tại chỗ và cự ly vận chuyển từ trạm trộn; chênh lệch vùng chủ yếu phản ánh giá cốt liệu địa phương.","xd.cat-da": "Cát, đá phụ thuộc mạnh vào cự ly mỏ – bãi – công trình và chính sách cấp phép khai thác từng địa phương, nên chênh lệch vùng thường lớn hơn các vật tư công nghiệp.",
        "xd.xi-mang": "Xi măng là hàng công nghiệp phân phối rộng; chênh lệch chủ yếu do cước vận chuyển từ nhà máy (miền Bắc có nhiều nhà máy hơn) và điều kiện giao hàng (tại nhà máy hay đến công trình).",
        "xd.cot-thep": "Thép dùng giá niêm yết nhà máy theo miền (Bắc ≈ Hà Nội, Nam ≈ TP.HCM); chênh lệch phản ánh chính sách giá vùng và cạnh tranh giữa các hãng."}
BASIS = {"rmc": "Giá niêm yết công khai trên website trạm trộn, chưa gồm bơm; chỉ so các bảng giá CHƯA VAT (bảng giá đã gồm VAT 8% như Mekong Thương Tín được loại khỏi phép so sánh). Cần chào giá thực tế theo khối lượng & cự ly.","steel": "Cùng nguồn (steelonline.vn), cùng ngày – so sánh trực tiếp được.",
         "sxd": "Khác cơ sở: Hà Nội = công bố giá Sở XD Q3/2026 (theo điểm giao cụ thể); TP.HCM = giá bình quân/tại mỏ tổng hợp hàng tháng – chỉ dùng tham khảo xu hướng."}
def build():
    prices = J(os.path.join(SITE, "prices.json"), {"items": []}); items = []
    for it in prices["items"]:
        h = J(os.path.join(SITE, "history", it["id"] + ".json"), {"points": []})
        pts = sorted([p for p in h.get("points", []) if p.get("price") is not None], key=lambda p: p["date"])
        last = pts[-1]["price"] if pts else it.get("price"); m, y = pt_at(pts, 30), pt_at(pts, 365)
        monthly = {}
        for p in pts: monthly[p["date"][:7]] = p["price"]
        ms = sorted(monthly.items())
        items.append(dict(id=it["id"], name=it["name"], unit=it["unit"], price=it.get("price"), price_high=it.get("price_high"),
            vnd=it.get("vnd"), vnd_unit=it.get("vnd_unit"), as_of=it.get("as_of"), src=it.get("src"), url=it.get("url"),
            stale=it.get("stale"), note=re.sub(r"(?<=\d),(?=\d{3}\b)", ".", it.get("note") or "") or None, category=it.get("category"), grp=it.get("grp"), region=it.get("region"),
            reg=region(it), tax=classify(it), d1=it.get("change_pct"), mom=pct(last, m and m["price"]), yoy=pct(last, y and y["price"]),
            n_hist=len(pts), spark=[p["price"] for p in pts[-90:]] if len(pts) >= 10 else None, first_date=pts[0]["date"] if pts else None,
            monthly=[dict(m=k, p=v, chg=pct(v, ms[i - 1][1]) if i else None) for i, (k, v) in enumerate(ms)]))
    # Hà Nội vs TP.HCM
    comps = []
    for label, rh, rc, tax, basis in PAIRS:
        hn = [x for x in items if x["reg"] == "hn" and x["tax"] == tax and re.search(rh, strip(x["name"])) and x["price"]]
        hc = [x for x in items if x["reg"] == "hcm" and x["tax"] == tax and re.search(rc, strip(x["name"])) and x["price"]]
        if basis == "rmc":  # compare like with like: drop price lists that already include VAT
            hn = [x for x in hn if "gom vat" not in strip(x.get("note"))]; hc = [x for x in hc if "gom vat" not in strip(x.get("note"))]
        hn = [x for x in hn if not x.get("stale")] or hn; hc = [x for x in hc if not x.get("stale")] or hc  # prefer live sources over stale fallbacks
        if not hn or not hc or hn[0]["unit"].replace("³", "3") != hc[0]["unit"].replace("³", "3"): continue
        a, b = mean(mid(x) for x in hn), mean(mid(x) for x in hc); d = pct(b, a)
        side = "TP.HCM cao hơn" if d > 0 else "TP.HCM thấp hơn"
        txt = (f"{side} Hà Nội {vn(abs(d), 1)}% ({vn(b)} so với {vn(a)} {hn[0]['unit']}). " if abs(d) >= 0.5 else
               f"Hai thị trường gần như ngang giá (chênh {'+' if d >= 0 else '−'}{vn(abs(d), 1)}%). ") + HINT.get(tax, "") + " " + BASIS[basis]
        if basis == "rmc":
            sup = lambda L: ", ".join(sorted({(re.search(r"\(([^)]+)\)\s*$", x["name"]) or [None, x["src"] or "?"])[1] for x in L}))
            txt += f" Nguồn so sánh – Hà Nội: {sup(hn)}; TP.HCM: {sup(hc)} (giá trị là trung bình các bảng giá, lấy điểm giữa nếu có khoảng)."
        comps.append(dict(label=label, tax=tax, unit=hn[0]["unit"], hn=round(a), hcm=round(b), diff_pct=d, insight=txt.strip(),
                          hn_ids=[x["id"] for x in hn], hcm_ids=[x["id"] for x in hc], basis=basis))
    # per-brand steel pairs (same brand both regions)
    brand = {}
    for x in items:
        if x["tax"] == "xd.cot-thep" and x["reg"] in ("hn", "hcm") and x["id"].startswith("vnsteel"): brand.setdefault(x["name"], {})[x["reg"]] = x
    brand_pairs = [dict(name=k, hn=v["hn"]["price"], hcm=v["hcm"]["price"], diff_pct=pct(v["hcm"]["price"], v["hn"]["price"]), unit=v["hn"]["unit"])
                   for k, v in sorted(brand.items()) if len(v) == 2]
    # monthly digest (trends + market + price MoM)
    T = J(os.path.join(H, "data", "trends.json"), {"items": []})["items"]; M = J(os.path.join(H, "data", "market.json"), {"items": []})["items"]
    months = sorted({x["date"][:7] for x in T + M}, reverse=True)[:12]; digest = []
    for mo in months:
        tm = sorted([x for x in T if x["date"][:7] == mo], key=lambda x: -x.get("score", 0)); mm = [x for x in M if x["date"][:7] == mo]
        digest.append(dict(month=mo, n_trends=len(tm), n_market=len(mm), top_trends=[dict(id=x["id"], title=x["title"], score=x["score"], category=x["category"]) for x in tm[:5]],
                           headlines=[dict(title=x["title"], url=x["sources"][0]["url"], region=x.get("region")) for x in mm[:6]]))
    movers = sorted([x for x in items if x["mom"] is not None], key=lambda x: -abs(x["mom"]))[:12]
    hub = dict(updated=prices.get("updated_at"), built=dt.datetime.now(TZ).isoformat(timespec="minutes"), usd_vnd=prices.get("usd_vnd"),
               items=items, compare=comps, steel_brand_pairs=brand_pairs, digest=digest, mom_movers=[x["id"] for x in movers])
    json.dump(hub, open(os.path.join(OUT, "hub.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return len(items), len(comps)
def main():
    os.makedirs(OUT, exist_ok=True)
    idx, gia = os.path.join(SITE, "index.html"), os.path.join(SITE, "gia.html")
    if os.path.exists(idx) and "data-hub-page" not in open(idx, encoding="utf-8").read(): shutil.move(idx, gia)
    for page, key in ((gia, "gia"), (os.path.join(SITE, "forecast.html"), "dubao")):  # inject shared nav into pages built by others
        if not os.path.exists(page): continue
        s = open(page, encoding="utf-8").read()
        if "hub-nav.css" not in s:
            s = s.replace("</head>", '<link rel="stylesheet" href="hub-nav.css"><script src="hub-common.js" defer></script></head>', 1)
            s = re.sub(r"<body([^>]*)>", lambda m: f'<body{m.group(1)} data-page="{key}"><div id="hubnav"></div>', s, count=1)
            s = s.replace('<a href="index.html">← Bảng giá</a>', '<a href="gia.html">← Bảng giá</a>')
            open(page, "w", encoding="utf-8").write(s)
    for f in glob.glob(os.path.join(H, "web", "*")): shutil.copy(f, SITE)
    for f in ("trends.json", "market.json", "feed.json", "scm.json", "segments.json"):
        if os.path.exists(os.path.join(H, "data", f)): shutil.copy(os.path.join(H, "data", f), OUT)
    shutil.copy(TAXF, os.path.join(OUT, "taxonomy.json"))
    # forecast page detection (built by the forecast worker): first match wins
    fc = next((p for p in ("du-bao.html", "du-bao/index.html", "forecast.html", "forecast/index.html") if os.path.exists(os.path.join(SITE, p))), None)
    json.dump(dict(forecast_page=fc), open(os.path.join(OUT, "site-config.json"), "w"))
    n, c = build(); print(f"hub built: {n} price items mapped, {c} HN/HCM comparisons, forecast page: {fc}")
if __name__ == "__main__": main()
