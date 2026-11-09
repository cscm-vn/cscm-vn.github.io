#!/usr/bin/env python3
"""Find Sở XD TP.HCM monthly material-price notices (công bố giá VLXD) and download the PDFs into probe/files/."""
import os, re, sys, json, hashlib, urllib.parse
from curl_cffi import requests as cr
from bs4 import BeautifulSoup
OUT = "probe/files"; os.makedirs(OUT, exist_ok=True)
def get(u):
    r = cr.get(u, impersonate="chrome", timeout=60, allow_redirects=True)
    print(f"GET {r.status_code} {len(r.content)//1024}kB {r.headers.get('content-type')} {u[:150]}"); return r
def links(u, pat):
    try: r = get(u)
    except Exception as e: print("ERR", u, e); return []
    s = BeautifulSoup(r.text, "html.parser"); out = []
    for a in s.find_all("a", href=True):
        h = urllib.parse.urljoin(u, a["href"]); t = " ".join(a.get_text(" ", strip=True).split())[:140]
        if re.search(pat, h + " " + t, re.I): out.append((h, t))
    seen = set(); res = []
    for h, t in out:
        if h in seen: continue
        seen.add(h); res.append((h, t)); print(f"LINK {u[8:60]} -> {h[:200]} | {t}")
    return res
# 1) official site
sxd = "https://soxaydung.hochiminhcity.gov.vn"
links(sxd + "/", r"gi[áa]|cong-bo|công bố|vat-lieu|vật liệu|kinh-te|kinh tế")
# 2) thuviennhadat topic + monthly articles -> PDF / drive links
arts = links("https://thuviennhadat.vn/chu-de/gia-vat-lieu-xay-dung-tphcm", r"gia-vat-lieu-xay-dung-tphcm-thang|dieu-chinh-bang-gia")
pdfs = []
for h, t in arts[:4]:
    for l, lt in links(h, r"\.pdf|drive\.google|docs\.google|soxaydung|TB-SXD|thong-bao"):
        pdfs.append(l)
# 3) download PDFs (cap 6)
saved = []
for p in list(dict.fromkeys(pdfs))[:6]:
    try:
        r = get(p)
        if r.status_code == 200 and (b"%PDF" in r.content[:1024]):
            fn = os.path.join(OUT, hashlib.md5(p.encode()).hexdigest()[:8] + ".pdf")
            open(fn, "wb").write(r.content); saved.append({"url": p, "file": fn, "kb": len(r.content)//1024}); print("SAVED", fn, p)
    except Exception as e: print("ERR", p, e)
json.dump(saved, open(os.path.join(OUT, "index.json"), "w"), ensure_ascii=False, indent=1)
