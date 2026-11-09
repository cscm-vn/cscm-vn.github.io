#!/usr/bin/env python3
"""Find the appendices (Phụ lục) of Sở XD TP.HCM monthly price notices: official Thong-bao page + the Google Drive folders
linked by thuviennhadat.vn. Download appendix files into probe/files/ for offline inspection."""
import os, re, json, urllib.parse
from curl_cffi import requests as cr
from bs4 import BeautifulSoup
OUT = "probe/files"; os.makedirs(OUT, exist_ok=True)
def get(u, **kw):
    r = cr.get(u, impersonate="chrome", timeout=90, allow_redirects=True, **kw)
    print(f"GET {r.status_code} {len(r.content)//1024}kB {r.headers.get('content-type')} {u[:160]}"); return r
# 1) official notices page
for u in ["https://soxaydung.hochiminhcity.gov.vn/Tin-tuc/Thong-bao", "https://soxaydung.hochiminhcity.gov.vn/"]:
    try:
        r = get(u); s = BeautifulSoup(r.text, "html.parser")
        print("OFFICIAL title:", s.title.string if s.title else None, "| text:", " ".join(s.get_text(" ", strip=True).split())[:600])
        for a in s.find_all("a", href=True):
            t = " ".join(a.get_text(" ", strip=True).split())
            if re.search(r"gi[áa]|vật liệu|VLXD|TB-SXD", t + a["href"], re.I): print("OFFICIAL LINK", urllib.parse.urljoin(u, a["href"])[:200], "|", t[:150])
        for sc in re.findall(r'src="([^"]+\.js[^"]*)"', r.text)[:10]: print("OFFICIAL JS", sc)
    except Exception as e: print("ERR", u, e)
# 2) Drive folders (Sept + Aug notices)
FOLDERS = {"t9": "1HK3xm5WrTa0cJ6iQO3emIGNBOdcQotIc", "t8": "1I2aWZSRL9X5F4Sxlp-n3E1BJI2w-9CHb"}
saved = []
for tag, fid in FOLDERS.items():
    try:
        h = get(f"https://drive.google.com/drive/folders/{fid}").text
        open(os.path.join(OUT, f"drive_{tag}.html"), "w").write(h)
        files = dict(re.findall(r'\\?"([\w-]{25,60})\\?",\[\\?"%s\\?"\],\\?"([^"\\]+)' % fid, h))
        if not files:  # fallback pattern: data-id + aria-label
            files = dict(re.findall(r'data-id="([\w-]{25,60})"[^>]*?aria-label="([^"]+)"', h))
        print(f"DRIVE {tag} files={len(files)}")
        for i, (did, name) in enumerate(files.items()):
            print(f"DRIVE {tag} {did} | {name}")
            if not re.search(r"(?i)ph[uụ] ?l[uụ]c|PL|\.xlsx?|\.pdf", name): continue
            try:
                r = get(f"https://drive.usercontent.google.com/download?id={did}&export=download&confirm=t")
                ext = ".pdf" if r.content[:4] == b"%PDF" else (".xlsx" if r.content[:2] == b"PK" else ".bin")
                fn = os.path.join(OUT, f"{tag}_{i:02d}{ext}")
                if ext != ".bin":
                    open(fn, "wb").write(r.content); saved.append({"tag": tag, "id": did, "name": name, "file": fn, "kb": len(r.content)//1024})
                    print("SAVED", fn, name)
            except Exception as e: print("ERR dl", did, e)
    except Exception as e: print("ERR folder", tag, e)
json.dump(saved, open(os.path.join(OUT, "drive_index.json"), "w"), ensure_ascii=False, indent=1)
