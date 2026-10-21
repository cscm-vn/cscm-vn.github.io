#!/usr/bin/env python3
"""Free automated news pull (runs in GitHub Actions + locally): Google News RSS (vi/en/zh) + VnExpress/CafeF/CafeLand RSS.
Writes trends/data/feed.json (rolling 45 days, dedup by URL/title), each item auto-tagged to taxonomy and keyword-scored.
Never raises: on any source error it keeps the previous items."""
import json, os, re, sys, time, hashlib, unicodedata, datetime as dt, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"); OUT = os.path.join(D, "feed.json")
TZ = dt.timezone(dt.timedelta(hours=7))
GN = "https://news.google.com/rss/search?q={q}&hl={hl}&gl={gl}&ceid={gl}:{lang}"
Q = [  # (query, hl, gl, lang, kind)
 ("giá thép xây dựng when:7d", "vi", "VN", "vi", "market"), ("giá vật liệu xây dựng when:7d", "vi", "VN", "vi", "market"),
 ("thị trường căn hộ Hà Nội when:7d", "vi", "VN", "vi", "market"), ("thị trường căn hộ TP.HCM when:7d", "vi", "VN", "vi", "market"),
 ("trúng thầu tổng thầu xây dựng when:7d", "vi", "VN", "vi", "market"), ("chống bán phá giá Bộ Công Thương when:14d", "vi", "VN", "vi", "trend"),
 ("thiết bị vệ sinh thông minh when:14d", "vi", "VN", "vi", "trend"), ("công trình xanh EDGE LOTUS when:14d", "vi", "VN", "vi", "trend"),
 ("thang máy chung cư when:14d", "vi", "VN", "vi", "trend"), ("nhà thông minh căn hộ cao cấp when:14d", "vi", "VN", "vi", "trend"),
 ("Canton Fair building materials sanitary when:14d", "en", "US", "en", "trend"), ("smart toilet market when:14d", "en", "US", "en", "trend"),
 ("sintered stone OR porcelain slab Foshan when:30d", "en", "US", "en", "trend"), ("low carbon cement OR green steel Vietnam when:30d", "en", "US", "en", "trend"),
 ("Vietnam construction materials when:7d", "en", "US", "en", "market"), ("LME aluminium copper price when:3d", "en", "US", "en", "trend"),
 ("佛山 陶瓷 出口 when:14d", "zh-CN", "CN", "zh-Hans", "trend"), ("智能马桶 出口 when:14d", "zh-CN", "CN", "zh-Hans", "trend"),
 ("建材 出口 越南 when:30d", "zh-CN", "CN", "zh-Hans", "trend"),
]
RSS = [("VnExpress Bất động sản", "https://vnexpress.net/rss/bat-dong-san.rss", "market"), ("CafeF Bất động sản", "https://cafef.vn/bat-dong-san.rss", "market"),
       ("CafeLand", "https://cafeland.vn/rss/tin-tuc.rss", "market"), ("VnExpress Kinh doanh", "https://vnexpress.net/rss/kinh-doanh.rss", "market")]
KW = {  # keyword -> weight (accent-free, lower)
 "masterise": 6, "can ho": 2, "ha noi": 2, "tp.hcm": 2, "tphcm": 2, "hang sang": 3, "cao cap": 2, "gia thep": 3, "vat lieu": 3, "xi mang": 2,
 "chong ban pha gia": 4, "trung thau": 3, "tong thau": 3, "nguon cung": 2, "gia ban": 2, "lai suat": 2, "chi so gia xay dung": 4,
 "smart toilet": 4, "sanitary": 3, "canton": 4, "foshan": 3, "sintered": 3, "tile": 2, "cement": 2, "green steel": 3, "low carbon": 3,
 "aluminium": 2, "copper": 2, "lme": 2, "vietnam": 2, "thang may": 3, "nha thong minh": 3, "edge": 2, "lotus": 2, "cong trinh xanh": 3,
 "佛山": 3, "陶瓷": 3, "智能马桶": 4, "出口": 2, "越南": 3, "建材": 3, "卫浴": 3,
}
def strip(s):
    s = unicodedata.normalize("NFD", (s or "").lower()); return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
def tax_rules():
    t = json.load(open((os.path.join(os.path.dirname(os.path.dirname(D)), "data", "taxonomy.json") if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(D)), "data", "taxonomy.json")) else os.path.join(D, "taxonomy.json")), encoding="utf-8"))
    return [(c["id"], [strip(k) for k in c.get("match", {}).get("kw", [])]) for n in t["tree"] for c in n["children"]]
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (price-dashboard feed bot)"})
    return urllib.request.urlopen(req, timeout=20).read()
def parse(xml, src, kind):
    out = []
    for it in ET.fromstring(xml).iter("item"):
        title = (it.findtext("title") or "").strip(); link = (it.findtext("link") or "").strip()
        s = it.find("source"); name = s.text.strip() if s is not None and s.text else src
        if name and title.endswith(" - " + name): title = title[: -len(name) - 3]
        try: d = parsedate_to_datetime(it.findtext("pubDate")).astimezone(TZ).date().isoformat()
        except Exception: d = dt.datetime.now(TZ).date().isoformat()
        desc = re.sub("<[^>]+>", " ", it.findtext("description") or ""); desc = re.sub(r"\s+", " ", desc).strip()[:300]
        if title and link: out.append(dict(title=title, url=link, source=name, date=d, kind=kind, snippet=desc if desc != title else ""))
    return out
def main():
    old = json.load(open(OUT, encoding="utf-8"))["items"] if os.path.exists(OUT) else []
    rules = tax_rules(); new = []; errs = []
    jobs = [(GN.format(q=urllib.parse.quote(q), hl=hl, gl=gl, lang=lang), "Google News", k) for q, hl, gl, lang, k in Q] + [(u, n, k) for n, u, k in RSS]
    for url, src, kind in jobs:
        try: new += parse(fetch(url), src, kind); time.sleep(0.5)
        except Exception as e: errs.append(f"{src}: {type(e).__name__}")
    cutoff = (dt.datetime.now(TZ) - dt.timedelta(days=45)).date().isoformat(); seen = set(); items = []
    for x in new + old:
        key = re.sub(r"\W+", " ", strip(x["title"])).strip()[:80]
        if x["date"] < cutoff or key in seen or x["url"] in seen: continue
        seen.update([key, x["url"]]); t = strip(x["title"] + " " + x.get("snippet", ""))
        x["tax"] = [cid for cid, kws in rules if any(k and k in t for k in kws)][:3]
        age = (dt.date.fromisoformat(dt.datetime.now(TZ).date().isoformat()) - dt.date.fromisoformat(x["date"])).days
        x["score"] = sum(w for k, w in KW.items() if k in t) + 2 * len(x["tax"]) - age * 0.3
        x["id"] = hashlib.sha1(x["url"].encode()).hexdigest()[:12]; x["origin"] = "rss"; items.append(x)
    items.sort(key=lambda x: (x["date"], x["score"]), reverse=True); items = items[:600]
    json.dump(dict(updated=dt.datetime.now(TZ).isoformat(timespec="minutes"), errors=errs, count=len(items), items=items),
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"feed: {len(new)} fetched, {len(items)} kept, errors: {errs or 'none'}")
if __name__ == "__main__":
    try: main()
    except Exception as e: print("feed failed (non-fatal):", e); sys.exit(0)
