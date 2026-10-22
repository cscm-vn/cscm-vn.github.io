#!/usr/bin/env python3
"""'Mới cập nhật' scanner for hop-dong.html: Google News RSS + official RSS for new construction-law / contract / trade-remedy items.
Writes trends/data/legal-feed.json (rolling 60 days). Every item is flagged reviewed=false – it is NOT curated content
(curated items live in legal.json / trade-remedies.json / disputes.json, maintained via trends/hopdong/build_data.py).
Never raises: on any source error it keeps previous items and records the error."""
import json, os, re, hashlib, unicodedata, datetime as dt, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"); OUT = os.path.join(D, "legal-feed.json")
TZ = dt.timezone(dt.timedelta(hours=7)); KEEP_DAYS = 60
GN = "https://news.google.com/rss/search?q={q}&hl=vi&gl=VN&ceid=VN:vi"
Q = [  # (query, section)
 ("nghị định hợp đồng xây dựng when:14d", "legal"), ("Luật Xây dựng 2025 hướng dẫn when:14d", "legal"),
 ("Bộ Xây dựng thông tư mới when:14d", "legal"), ("Luật Đấu thầu sửa đổi nghị định when:14d", "legal"),
 ("chỉ số giá xây dựng điều chỉnh giá hợp đồng when:14d", "legal"), ("quản lý chi phí đầu tư xây dựng nghị định when:14d", "legal"),
 ("chống bán phá giá Bộ Công Thương thép when:14d", "trade"), ("phòng vệ thương mại khởi xướng điều tra when:14d", "trade"),
 ("chống bán phá giá nhôm kính gạch when:30d", "trade"), ("thuế nhập khẩu thép thuế GTGT thay đổi when:14d", "trade"),
 ("tranh chấp hợp đồng xây dựng nhà thầu chủ đầu tư when:14d", "dispute"), ("VIAC trọng tài xây dựng phán quyết when:30d", "dispute"),
 ("kiện đòi nợ thi công tổng thầu when:14d", "dispute"), ("FIDIC contract dispute Vietnam when:30d", "dispute"),
]
OFFICIAL = [  # official RSS (best effort)
 ("Chinhphu.vn – Chính sách mới", "https://xaydungchinhsach.chinhphu.vn/chinh-sach-moi.rss", "legal"),
]
REL = {  # accent-free keywords; an item must match its section's list
 "legal": ["hop dong xay dung", "luat xay dung", "bo xay dung", "dau thau", "nha thau", "chi phi dau tu xay dung", "chi so gia xay dung", "dieu chinh gia", "cong trinh xay dung", "giay phep xay dung", "quan ly chat luong cong trinh"],
 "trade": ["ban pha gia", "chong tro cap", "tu ve", "phong ve thuong mai", "lan tranh", "thue nhap khau", "thue gtgt", "thue gia tri gia tang"],
 "dispute": ["tranh chap hop dong", "trong tai", "viac", "kien doi", "khoi kien", "phan quyet trong tai", "fidic", "no thi cong", "cong no", "dispute", "arbitration"]}
def strip(s): return unicodedata.normalize("NFD", s.lower()).encode("ascii", "ignore").decode().replace("đ", "d")
def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MasteriseSCMHub/1.0)"})
    return urllib.request.urlopen(r, timeout=20).read()
def parse(xml, section, srcname):
    out = []
    for it in ET.fromstring(xml).iter("item"):
        t = (it.findtext("title") or "").strip(); u = (it.findtext("link") or "").strip()
        if not t or not u: continue
        pub = None
        try: pub = parsedate_to_datetime(it.findtext("pubDate")).astimezone(TZ).isoformat(timespec="minutes")
        except Exception: pass
        src = it.find("source"); name = src.text.strip() if src is not None and src.text else srcname
        if " - " in t and src is not None: t = t.rsplit(" - ", 1)[0]
        if not any(k in strip(t) for k in REL[section]): continue
        out.append(dict(id=hashlib.md5(strip(t).encode()).hexdigest()[:12], title=unicodedata.normalize("NFC", t), url=u, source=name,
                        section=section, published=pub, reviewed=False))
    return out
def main():
    old = {}
    try: old = json.load(open(OUT, encoding="utf-8"))
    except Exception: pass
    items = {x["id"]: x for x in old.get("items", [])}; errors = []; now = dt.datetime.now(TZ)
    for q, sec in Q:
        try:
            for x in parse(get(GN.format(q=urllib.parse.quote(q))), sec, "Google News"): items.setdefault(x["id"], {**x, "found": now.isoformat(timespec="minutes")})
        except Exception as e: errors.append(f"{q}: {type(e).__name__}")
    for name, url, sec in OFFICIAL:
        try:
            for x in parse(get(url), sec, name): items.setdefault(x["id"], {**x, "found": now.isoformat(timespec="minutes")})
        except Exception as e: errors.append(f"{name}: {type(e).__name__}")
    cut = (now - dt.timedelta(days=KEEP_DAYS)).isoformat()
    keep = sorted([x for x in items.values() if (x.get("published") or x.get("found") or "") >= cut], key=lambda x: x.get("published") or x.get("found") or "", reverse=True)[:400]
    json.dump(dict(schema_version=1, updated=now.isoformat(timespec="minutes"), note="Tin tự động – CHƯA biên tập/kiểm chứng (reviewed=false).", errors=errors, count=len(keep), items=keep),
              open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"legal feed: {len(keep)} items, {len(errors)} errors")
if __name__ == "__main__": main()
