#!/usr/bin/env python3
"""Quy đổi số tiền Nhân dân tệ (NDT/CNY/RMB/元/¥/yuan) trong tin tức sang VND khi build (không sửa dữ liệu gốc trends/data/).
Định dạng: "≈ 14,2 triệu đ/tấn (4.000 NDT/tấn)". Tỷ giá: CNY/VND Vietcombank (chuyển khoản) mới nhất do fetcher.py ghi
vào data/history/prices/YYYY-MM.csv (item fx_cny_vnd). Không có tỷ giá -> giữ nguyên văn bản. Số USD không bị động tới."""
import csv, glob, json, os, re, datetime as dt
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H)
FILES = ("trends.json", "market.json", "feed.json", "scm.json", "policy-feed.json", "legal-feed.json", "highlights.json", "hub.json", "trk.json")
SKIP_KEYS = {"url", "id", "link", "href", "src_url", "source_url", "sources_url", "image", "cluster", "tax", "l1"}

def rate():
    best = None
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "history", "prices", "*.csv")))[-2:]:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            if r.get("item_id") == "fx_cny_vnd" and r.get("price"):
                k = (r["date"], r.get("fetched_at") or "")
                if not best or k >= best[0]: best = (k, float(r["price"]), r["date"])
    return (best[1], best[2]) if best else (None, None)

def vn(v, d=0):
    s = f"{v:,.{d}f}"; return s.replace(",", "§").replace(".", ",").replace("§", ".")
def num(s):  # Vietnamese: dot = thousands, comma = decimal
    return float(s.replace(".", "").replace(",", "."))
def fmt(v):
    a = abs(v)
    if a >= 1e12: t = f"{vn(a/1e12, 2 if a < 1e13 else 1 if a < 1e14 else 0)} nghìn tỷ"
    elif a >= 1e9: t = f"{vn(a/1e9, 1 if a < 1e11 else 0)} tỷ"
    elif a >= 1e6: t = f"{vn(a/1e6, 2 if a < 1e7 else 1)} triệu"
    else: t = vn(round(a, -2) if a >= 1000 else round(a, -1))
    t = re.sub(r",0+(?= )|,0+$", "", t) if re.search(r",0+( |$)", t) else t
    return ("−" if v < 0 else "+" if v > 0 and SIGN[0] == "+" else "") + t
SIGN = [""]
SCALE = {"nghìn": 1e3, "ngàn": 1e3, "vạn": 1e4, "万": 1e4, "triệu": 1e6, "tỷ": 1e9, "亿": 1e8}
UNIT = {"tấn": "tấn", "t": "tấn", "吨": "tấn", "kg": "kg", "m²": "m²", "m2": "m²", "m³": "m³", "m3": "m³", "tấm": "tấm", "m": "m"}
N = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?"
RX = re.compile(r"(?<![\w.,/])(?P<tilde>~\s?)?(?P<sign>[+−]|-(?=\d))?(?P<a>" + N + r")(?:\s*[–—-]\s*(?P<b>" + N + r"))?"
                r"(?:\s*(?P<sc>nghìn|ngàn|vạn|triệu|tỷ|万|亿))?\s*(?P<cur>NDT|nhân dân tệ|元|CNY|RMB|yuan)(?![\w])"
                r"(?P<u>\s*/\s*(?:tấn|吨|kg|m²|m2|m³|m3|tấm|t|m)(?![\wáàảãạâấầẩẫậ]))?")
RXP = re.compile(r"(?<![\w])(?P<cur>¥|CNY|RMB)\s?(?P<a>" + N + r")(?:\s*[–—-]\s*(?P<b>" + N + r"))?(?:\s*(?P<sc>nghìn|triệu|tỷ|万|亿))?"
                 r"(?P<u>\s*/\s*(?:tấn|吨|kg|m²|m2|t)(?![\w]))?")

def convert(s, r):
    n = [0]
    def rep(m):
        if m.string[max(0, m.start() - 1):m.start()] == "(" and any(x.end() == len(m.string[:m.start() - 1].rstrip()) for x in RX.finditer(m.string[:m.start() - 1].rstrip())): return m.group(0)  # alias of an amount just converted
        a = m.group("a"); b = m.group("b"); sc = SCALE.get(m.group("sc") or "", 1)
        sg = m.groupdict().get("sign") or ""; SIGN[0] = "+" if sg == "+" else ""
        mul = -1 if sg in ("−", "-") else 1
        u = m.group("u"); us = "/" + UNIT[re.sub(r"[\s/]", "", u)] if u else ""
        va = mul * num(a) * sc * r
        txt = fmt(va)
        if b:
            tb = fmt(mul * num(b) * sc * r).lstrip("+"); ua, ub = txt.split(" ", 1)[1:] or [""], tb.split(" ", 1)[1:] or [""]
            txt = (txt.split(" ", 1)[0] + "–" + tb) if ua == ub and ua != [""] else (txt + "–" + tb)
        n[0] += 1
        return f"≈ {txt} đ{us} ({m.group(0).strip()})" if not m.groupdict().get("tilde") else f"≈ {txt} đ{us} ({m.group(0).strip()})"
    s2 = RX.sub(rep, s); s2 = RXP.sub(rep, s2) if "≈" not in s2 or RXP.search(s2) else s2
    return s2, n[0]

def walk(o, r, note, cnt, key=None):
    if isinstance(o, str):
        if key in SKIP_KEYS or "://" in o: return o
        s, k = convert(o, r); cnt[0] += k; return s
    if isinstance(o, list): return [walk(x, r, note, cnt) for x in o]
    if isinstance(o, dict):
        before = cnt[0]
        d = {k: walk(v, r, note, cnt, k) for k, v in o.items()}
        if cnt[0] > before and isinstance(d.get("summary"), str) and note not in d["summary"] and "title" in d:
            d["summary"] = d["summary"].rstrip() + f" (Quy đổi: {note}.)"; cnt[1] += 1
        return d
    return o

def apply(out_dir):
    r, day = rate()
    if not r: print("rmb_vnd: không có tỷ giá CNY/VND -> bỏ qua"); return 0
    dd = dt.date.fromisoformat(day); note = f"tỷ giá 1 NDT = {vn(r)} đ, Vietcombank ngày {dd:%d/%m}"
    tot = 0
    for f in FILES:
        p = os.path.join(out_dir, f)
        if not os.path.exists(p): continue
        raw = open(p, encoding="utf-8").read(); d = json.loads(raw); cnt = [0, 0]
        d = walk(d, r, note, cnt)
        if isinstance(d, dict): d["fx_cny_vnd"] = dict(rate=r, date=day, source="Vietcombank (chuyển khoản)", note=note) if cnt[0] else d.get("fx_cny_vnd")
        if cnt[0]:
            compact = "\n" not in raw[:200]
            json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, **(dict(separators=(",", ":")) if compact else dict(indent=1)))
        tot += cnt[0]; print(f"rmb_vnd: {f}: {cnt[0]} số tiền NDT quy đổi")
    print(f"rmb_vnd: tổng {tot} ({note})"); return tot

if __name__ == "__main__":
    import sys; r, _ = rate()
    for t in sys.argv[1:]: print(convert(t, r)[0])
