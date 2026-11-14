#!/usr/bin/env python3
"""Thăm dò nguồn giá mới (chạy tay trên GitHub Actions: workflow 'probe-sources'). Chỉ IN ra, không ghi dữ liệu.
Dùng khi cần thay nguồn đứng giá: liệt kê phụ lục công bố giá Sở XD TP.HCM và in mẫu dòng; tải thử trang web ứng viên."""
import os, re, sys, io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import hcm_sxd as H

def sxd(nmonths=2, want=r"thep|be tong|cap|day dien|gach|vua|nhe|aac|ong|son|kinh|nhom"):
    for n in H.latest_notices(nmonths):
        print("\n=== SXD", n["month"], n.get("tb"), n.get("issued"), n.get("drive"))
        files = H.drive_files(n["drive"])
        for did, name in files: print("  file:", did, name)
        for did, name in files:
            if not re.search(want, H.ascii_(name)): continue
            try:
                import pdfplumber
                b = H.drive_pdf(did)
                with pdfplumber.open(io.BytesIO(b)) as p:
                    t = H.nfc(p.pages[0].extract_text() or "")
                    print(f"\n--- {name} pages={len(p.pages)}\n{t[:500]}")
                    k = 0
                    for pg in p.pages[:3]:
                        for tb in pg.extract_tables():
                            for r in tb:
                                c = [H.nfc((x or "").replace("\n", " ")).strip() for x in r]
                                if k < 25: print("   ROW", len(c), c); k += 1
            except Exception as e: print("  ERR", name, e)

def web(urls):
    from curl_cffi import requests as cr
    for u in urls:
        try:
            r = cr.get(u, impersonate="chrome", timeout=40)
            t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", re.sub(r"(?s)<(script|style).*?</\1>", " ", r.text)))
            print(f"\n=== WEB {r.status_code} {u} len={len(t)}")
            for kw in ("CB240", "CB300", "D10", "CXV", "1x95", "1×95", "M300", "M250", "cập nhật", "Cập nhật", "ngày", "2026"):
                for m in list(re.finditer(re.escape(kw), t))[:3]: print(f"  [{kw}] …{t[max(0, m.start()-120):m.end()+160]}…")
        except Exception as e: print("=== WEB ERR", u, e)

def rows(nmonths=2, want=r"thep|cap dien|be tong thuong|vua|^phu ?luc \\d+\\.pdf$"):
    """In TẤT CẢ dòng của phụ lục thép / dây cáp điện / bê tông thương phẩm / vữa (nhận diện theo tiêu đề trang 1)."""
    import json
    H.KINDS.update({"thep": "thép xây dựng", "cap": "vật tư ngành điện", "be_tong": "bê tông thương phẩm", "vua": "vữa"})
    for n in H.latest_notices(nmonths):
        print("\n=== SXD", n["month"], n.get("tb"), n.get("issued"))
        for did, name in H.drive_files(n["drive"]):
            if not re.search(want, H.ascii_(name)): continue
            try:
                kind, title, rr = H.table_rows(H.drive_pdf(did))
                if kind not in ("thep", "cap", "be_tong", "vua"): continue
                print(f"--- {kind} {name} n={len(rr)}")
                for r in rr: print("R", json.dumps([kind, r["section"], r["name"], r["unit"], r["spec"], r["supplier"][:60], r["cond"][:80], r["note"][:40], r["prices"]], ensure_ascii=False))
            except Exception as e: print("  ERR", name, e)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rows": rows(); sys.exit()
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode in ("all", "sxd"): sxd()
    if mode in ("all", "web"): web([l.strip() for l in open(os.path.join(os.path.dirname(__file__), "probe_urls.txt")) if l.strip() and not l.startswith("#")])
