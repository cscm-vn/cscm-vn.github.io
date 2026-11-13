#!/usr/bin/env python3
"""Tin thương hiệu tự động cho tab "Thương hiệu" (danh-muc.html): Google News RSS (vi/VN) theo từng danh mục trong trends/data/brands.json.
Mỗi danh mục: gộp tên hãng thành truy vấn ("A" OR "B" …) + ngữ cảnh danh mục (cats[c].ctx), tối đa CHUNK hãng/truy vấn.
Chỉ giữ tin có tiêu đề nêu đúng một hãng của danh mục đó (kws không dấu, khớp nguyên từ). Ghi trends/data/brand-feed.json (cuộn KEEP_DAYS ngày).
Tin tự động – CHƯA biên tập; phần tóm tắt biên tập nằm ở brands.json (digest), cập nhật bằng lịch tuần.
Không bao giờ raise: nguồn lỗi được ghi vào errors và giữ tin cũ."""
import json, os, re, sys, time, hashlib, unicodedata, datetime as dt, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"); OUT = os.path.join(D, "brand-feed.json"); REG = os.path.join(D, "brands.json")
TZ = dt.timezone(dt.timedelta(hours=7)); KEEP_DAYS = 90; CAP = 2500; CHUNK = 6
GN = "https://news.google.com/rss/search?q={q}&hl=vi&gl=VN&ceid=VN:vi"
def strip(s):
    s = unicodedata.normalize("NFD", (s or "").lower()); return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
def rx(ks): return re.compile(r"(?<![a-z0-9])(?:" + "|".join(re.escape(strip(k)) for k in ks) + r")(?![a-z0-9])")
def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MasteriseSCMHub/1.0)"})
    return urllib.request.urlopen(r, timeout=20).read()
def parse(xml):
    for it in ET.fromstring(xml).iter("item"):
        t = (it.findtext("title") or "").strip(); u = (it.findtext("link") or "").strip()
        if not t or not u: continue
        s = it.find("source"); name = s.text.strip() if s is not None and s.text else "Google News"
        if name and t.endswith(" - " + name): t = t[: -len(name) - 3]
        try: d = parsedate_to_datetime(it.findtext("pubDate")).astimezone(TZ).date().isoformat()
        except Exception: d = dt.datetime.now(TZ).date().isoformat()
        yield dict(title=unicodedata.normalize("NFC", t), url=u, source=name, date=d)
def jobs(reg):
    """[(category, [brand ids], query url)] – quoted names lấy từ trường query của từng hãng."""
    out = []
    for c, meta in reg.get("cats", {}).items():
        bs = [b for b in reg["brands"] + reg.get("emerging", []) if c in b["tax"] and b.get("query") and b.get("kws")]  # + hãng mới nổi
        for i in range(0, len(bs), CHUNK):
            part = bs[i:i + CHUNK]; names = [n for b in part for n in re.findall(r'"[^"]+"', b["query"])]
            ctx = [w.strip().strip('"') for w in meta.get("ctx", "").strip("() ").split(" OR ") if w.strip()]
            ctx = ("(" + " OR ".join(f'"{w}"' if " " in w else w for w in ctx) + ") ") if ctx else ""  # cụm nhiều từ phải trong ngoặc kép, nếu không OR chỉ gắn với từ kề bên
            q = "(" + " OR ".join(names) + ") " + ctx + "when:30d"
            out.append((c, [b["id"] for b in part], GN.format(q=urllib.parse.quote(q))))
    return out
def main():
    reg = json.load(open(REG, encoding="utf-8")); RX = {b["id"]: rx(b["kws"]) for b in reg["brands"] + reg.get("emerging", []) if b.get("kws")}
    old = {}
    try: old = json.load(open(OUT, encoding="utf-8"))
    except Exception: pass
    items = {x["id"]: x for x in old.get("items", [])}; errors = []; now = dt.datetime.now(TZ); n_new = 0
    for c, bids, url in jobs(reg):
        try:
            for x in parse(get(url)):
                t = strip(x["title"]); hit = [b for b in bids if RX[b].search(t)]
                if not hit: continue  # tiêu đề không nêu hãng nào của danh mục → bỏ (Google trả nhiều tin chỉ khớp ngữ cảnh)
                key = hashlib.sha1(re.sub(r"\W+", " ", t).strip()[:80].encode()).hexdigest()[:12]
                y = items.get(key)
                if y is None: y = items[key] = dict(id=key, **x, brands=[], tax=[], found=now.isoformat(timespec="minutes")); n_new += 1
                y["brands"] = sorted(set(y["brands"]) | set(hit)); y["tax"] = sorted(set(y["tax"]) | {c})
            time.sleep(0.5)
        except Exception as e: errors.append(f"{c}: {type(e).__name__}")
    cut = (now - dt.timedelta(days=KEEP_DAYS)).date().isoformat()
    keep = sorted([x for x in items.values() if x["date"] >= cut], key=lambda x: (x["date"], x.get("found", "")), reverse=True)[:CAP]
    json.dump(dict(schema_version=1, updated=now.isoformat(timespec="minutes"), note="Tin tự động theo thương hiệu – CHƯA biên tập/kiểm chứng.",
                   errors=errors, count=len(keep), items=keep), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"brand feed: {len(keep)} items ({n_new} new), {len(errors)} errors{': ' + ', '.join(errors[:5]) if errors else ''}")
if __name__ == "__main__":
    try: main()
    except Exception as e: print("brand feed failed (non-fatal):", type(e).__name__, e); sys.exit(0)
