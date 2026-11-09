#!/usr/bin/env python3
"""One-off reachability probe from a GitHub runner: fetch candidate HCM material-price sources with
plain requests and with curl_cffi (Chrome TLS impersonation), save status + body for offline inspection."""
import json, os, re, sys, time, hashlib
import requests
OUT = sys.argv[1] if len(sys.argv) > 1 else "probe_out"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8", "Accept-Language": "vi,en;q=0.8"}
URLS = [
 "https://www.thitruonghanghoa.com/gia-ca-thi-truong-viet-nam/gia-xi-mang-hom-nay",
 "https://thuviennhadat.vn/chu-de/gia-vat-lieu-xay-dung-tphcm",
 "https://thuviennhadat.vn/bat-dong-san-360/gia-vat-lieu-xay-dung-tphcm-thang-9-2026-748678.html",
 "https://thuviennhadat.vn/bat-dong-san-360/gia-vat-lieu-xay-dung-tphcm-thang-8-2026-747371.html",
 "https://soxaydung.hochiminhcity.gov.vn/",
 "https://soxaydung.hochiminhcity.gov.vn/web/guest/tim-kiem?q=c%C3%B4ng+b%E1%BB%91+gi%C3%A1",
 "https://kinhtexaydung.gov.vn/wp-json/wp/v2/media?search=H%E1%BB%93+Ch%C3%AD+Minh&per_page=50",
 "https://kinhtexaydung.gov.vn/wp-json/wp/v2/media?search=HCM&per_page=50",
 "https://kinhtexaydung.gov.vn/wp-json/wp/v2/media?search=TPHCM&per_page=50",
 "https://kinhtexaydung.gov.vn/wp-json/wp/v2/posts?search=H%E1%BB%93+Ch%C3%AD+Minh&per_page=30",
 "https://thuvienphapluat.vn/phap-luat-nha-dat/bang-gia-vat-lieu-xay-dung-tphcm-thang-6-2026-theo-cong-bo-moi-nhat-17245.html",
 "https://news.google.com/rss/search?q=%22c%C3%B4ng+b%E1%BB%91+gi%C3%A1%22+v%E1%BA%ADt+li%E1%BB%87u+x%C3%A2y+d%E1%BB%B1ng+TP.HCM+when:60d&hl=vi&gl=VN&ceid=VN:vi",
 "https://news.google.com/rss/search?q=TB-SXD-KTVLXD+when:90d&hl=vi&gl=VN&ceid=VN:vi",
]
def fname(u): return re.sub(r"[^a-z0-9]+", "_", u.lower())[8:90] + "_" + hashlib.md5(u.encode()).hexdigest()[:6]
res = []
try:
    from curl_cffi import requests as cr
except Exception as e:
    cr = None; print("curl_cffi missing", e)
for u in URLS:
    for mode in ("requests", "curl_cffi"):
        rec = {"url": u, "mode": mode}
        try:
            t = time.time()
            if mode == "requests": r = requests.get(u, headers=UA, timeout=40)
            else:
                if not cr: continue
                r = cr.get(u, impersonate="chrome", timeout=40)
            rec.update(status=r.status_code, bytes=len(r.content), secs=round(time.time() - t, 1),
                       ctype=r.headers.get("content-type"), server=r.headers.get("server"), final=str(r.url))
            fn = f"{mode}_{fname(u)}"
            open(os.path.join(OUT, fn), "wb").write(r.content); rec["file"] = fn
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"[:300]
        print(json.dumps(rec, ensure_ascii=False)); res.append(rec)
json.dump(res, open(os.path.join(OUT, "summary.json"), "w"), ensure_ascii=False, indent=1)
