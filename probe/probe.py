#!/usr/bin/env python3
"""Probe from a GitHub runner: for each source URL, compare python-requests vs curl_cffi (Chrome) — status, size, <table> present."""
import requests
from curl_cffi import requests as cr
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept-Language": "vi,en;q=0.8"}
URLS = ["https://www.thitruonghanghoa.com/gia-ca-thi-truong-viet-nam/gia-xi-mang-hom-nay",
        "https://www.thitruonghanghoa.com/gia-ca-thi-truong-viet-nam/gia-cat-xay-dung-hom-nay",
        "https://www.thitruonghanghoa.com/gia-ca-thi-truong-viet-nam/gia-da-xay-dung-hom-nay",
        "https://www.thitruonghanghoa.com/gia-ca-thi-truong-viet-nam/gia-gach-xay-dung-hom-nay",
        "https://betonghanoi.com.vn/", "https://betongtuoichem.com/", "https://betongdvc.com/bao-gia-be-tong-tuoi-tp-hcm/",
        "https://betongdongnam.com/cap-nhat-gia-be-tong-tuoi-tphcm-nhanh/", "https://mekongthuongtin.com/gia-be-tong-tuoi/",
        "https://anx.vn/gia-gach-xay-nha.html", "https://thanhdattech.com.vn/bang-gia-day-cap-dien-cxv-cadivi-06-1kv/"]
for u in URLS:
    row = [u[8:70]]
    for name, f in (("req", lambda: requests.get(u, headers=UA, timeout=30)), ("chrome", lambda: cr.get(u, impersonate="chrome", timeout=30))):
        try:
            r = f(); t = r.text
            row.append(f"{name}={r.status_code} {len(t)//1000}kB tables={t.lower().count('<table')} cf={'just a moment' in t.lower()}")
        except Exception as e: row.append(f"{name}=ERR {type(e).__name__}")
    print("PROBE |", " | ".join(row))
