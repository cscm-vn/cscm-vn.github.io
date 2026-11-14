#!/usr/bin/env python3
"""Giá VLXD TP.HCM từ CÔNG BỐ GIÁ HẰNG THÁNG của Sở Xây dựng TP.HCM (Thông báo .../TB-SXD-KTVLXD + Phụ lục).
Thay nguồn thitruonghanghoa.com (đã ngừng đăng dữ liệu xi măng/cát/đá/gạch từ 10/2026).

Luồng: thuviennhadat.vn (trang chủ đề, đăng lại mỗi thông báo kèm link PDF + thư mục Google Drive chứa Phụ lục)
  -> liệt kê file trong thư mục Drive -> tải Phụ lục xi măng / gạch không nung / đá / cát (nhận diện theo TIÊU ĐỀ trang 1,
  vì số thứ tự phụ lục đổi theo tháng) -> đọc bảng (pdfplumber) -> gộp thành dòng giá cùng id với nguồn cũ (vnmat_*).
Trang Sở XD (soxaydung.hochiminhcity.gov.vn) chặn máy chủ GitHub (WAF), nên dùng bản đăng lại; số liệu là của Sở XD.
Kết quả mỗi thông báo được lưu data/hcm_sxd/YYYY-MM.json (commit), lần chạy sau không tải lại.
Quy tắc gộp (giữ đúng định nghĩa chuỗi cũ, đã đối chiếu TB 32431 tháng 8/2026):
  - Xi măng: theo mác (PCB30/40/50, PC40, MC25) + loại (bền sunfat / xỉ lò cao) + đóng gói (bao/rời); cột Khu vực 1;
    giá theo bao quy ra tấn; dòng không rõ bao/rời bị bỏ. price = thấp nhất, price_high = cao nhất giữa các NCC.
  - Cát, đá: mục "Giá bình quân khu vực" lấy nguyên giá Sở công bố; mục "Giá tại mỏ" = khoảng thấp–cao giữa TẤT CẢ các mỏ
    trong phụ lục (từ 9/2026; nguồn cũ bỏ sót một số mỏ nên giá thấp trước đó cao hơn), bỏ đá phong hoá và loại 4–5.
    Tên quy về: 1x2 (gồm 10x20 mm), 2x4 (20x40), 4x6 (40x60), cấp phối đá dăm Dmax 25 / 37,5 (gồm "Đá Dmax ...").
  - Gạch không nung: theo loại (block / ống / đinh / đặc / tự chèn / trồng cỏ) + kích thước.
Không bịa giá: không đọc được => raise, fetcher giữ giá cũ và gắn cờ "cũ"."""
import os, re, io, sys, json, html, unicodedata, datetime as dt, urllib.parse

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "data", "hcm_sxd")
NBACK = 4  # số thông báo gần nhất được đọc/bổ sung (lịch sử thép/cáp/bê tông/vữa)
TOPIC = "https://thuviennhadat.vn/chu-de/gia-vat-lieu-xay-dung-tphcm"
REGION = "TP. Hồ Chí Minh"
KINDS = {"xi_mang": "xi măng", "gach": "gạch không nung", "da": "đá xây dựng", "cat": "cát xây dựng"}
# Phụ lục bổ sung (từ 11/2026): thay nguồn web đại lý/NCC đứng giá. Không bắt buộc – thiếu thì bỏ qua, không làm hỏng xi măng/cát/đá/gạch.
EXTRA = {"thep": "thép xây dựng", "cap": "vật tư ngành điện", "be_tong": "bê tông thương phẩm", "vua": "vữa"}

def _http(url, binary=False):
    """GET as Chrome (curl_cffi) – thuviennhadat/Drive sit behind bot rules; fall back to requests."""
    try:
        from curl_cffi import requests as cr
        r = cr.get(url, impersonate="chrome", timeout=90, allow_redirects=True)
    except ImportError:
        import requests
        r = requests.get(url, timeout=90, headers={"User-Agent": "Mozilla/5.0 Chrome/124"})
    if r.status_code >= 400: raise RuntimeError(f"HTTP {r.status_code} {url[:120]}")
    return r.content if binary else r.text

def nfc(s): return unicodedata.normalize("NFC", s or "")
def ascii_(s): return unicodedata.normalize("NFKD", nfc(s).replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode().lower()
def slug(t): return re.sub(r"[^a-z0-9]+", "_", ascii_(t)).strip("_")
def vnd(s):
    s = re.sub(r"[^\d]", "", s or "")
    return float(s) if s else None

# ---------------- discovery ----------------
def latest_notices(n=2):
    """Newest monthly notices from the topic page: [{month:'YYYY-MM', article, pdf, tb, drive, issued}] newest first."""
    from bs4 import BeautifulSoup
    s = BeautifulSoup(_http(TOPIC), "html.parser"); arts = []
    for a in s.find_all("a", href=True):
        m = re.search(r"/gia-vat-lieu-xay-dung-tphcm-thang-(\d{1,2})-(\d{4})-\d+\.html", a["href"])
        if m:
            u = urllib.parse.urljoin(TOPIC, a["href"]); k = f"{m.group(2)}-{int(m.group(1)):02d}"
            if k not in [x[0] for x in arts]: arts.append((k, u))
    arts.sort(reverse=True); out = []
    for k, u in arts[:n]:
        h = _http(u); s = BeautifulSoup(h, "html.parser"); d = {"month": k, "article": u}
        for a in s.find_all("a", href=True):
            href = a["href"]
            if "drive.google.com/drive/folders/" in href and "drive" not in d: d["drive"] = href.split("?")[0]
            if href.lower().endswith(".pdf") and "pdf" not in d: d["pdf"] = urllib.parse.urljoin(u, href)
        txt = " ".join(s.get_text(" ", strip=True).split())
        m = re.search(r"(?:Thông báo|TB)\s*(?:số\s*)?(\d{4,6})/TB-SXD", txt); d["tb"] = m.group(1) if m else None
        m = re.search(r"[Nn]gày\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})\s*,?\s*Sở Xây dựng", txt)
        if m: d["issued"] = f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
        if "drive" in d: out.append(d)
    return out

def drive_files(folder_url):
    """Public Drive folder -> [(file_id, name)] from the folder page markup."""
    fid = folder_url.rstrip("/").split("/")[-1]
    h = _http(f"https://drive.google.com/drive/folders/{fid}"); res = []
    for did, chunk in re.findall(r'data-id="([\w-]{25,})"(.*?)(?=data-id="[\w-]{25,}"|$)', h, re.S):
        m = re.search(r'aria-label="([^"]+?\.pdf)', chunk)
        if m and did not in [x[0] for x in res]: res.append((did, nfc(html.unescape(m.group(1)))))
    if not res: raise RuntimeError("Drive: không đọc được danh sách file")
    return res

def drive_pdf(did):
    b = _http(f"https://drive.usercontent.google.com/download?id={did}&export=download&confirm=t", binary=True)
    if b[:4] != b"%PDF": raise RuntimeError(f"Drive {did}: không phải PDF")
    return b

# ---------------- PDF tables ----------------
def appendix_kind(first_page_text):
    t = ascii_(first_page_text[:400])
    for k, v in {**KINDS, **EXTRA}.items():
        if re.search(r"cong bo gia san pham " + ascii_(v) + r"\b", t): return k
    return None

def table_rows(pdf_bytes):
    """-> (kind, title, [dict(section, name, unit, spec, supplier, cond, note, prices[])])"""
    import pdfplumber
    rows, sec, kind, title = [], None, None, ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as p:
        title = nfc(p.pages[0].extract_text() or ""); kind = appendix_kind(title)
        if not kind: return None, title, []
        for pg in p.pages:
            for t in pg.extract_tables():
                for r in t:
                    c = [nfc((x or "").replace("\n", " ")).strip() for x in r]
                    if len(c) < 12: continue
                    if not any(c[:3]) and c[-1] and not re.search(r"\d", c[-1]): sec = c[-1]; continue
                    if not re.fullmatch(r"\d+", c[0]): continue
                    sup = c[6] if c[6] and c[6] not in ('"', "“", "”", "''") else (rows[-1]["supplier"] if rows else "")
                    rows.append(dict(section=sec, name=c[2], unit=c[3], std=c[4], spec=c[5], supplier=sup, cond=c[8], note=c[10],
                                     prices=[vnd(x) for x in c[11:]]))
    return kind, title, rows

# ---------------- aggregation ----------------
def cement_key(r):
    n = ascii_(r["name"]); u = ascii_(r["unit"]); q = ascii_(r["spec"])
    n2 = re.sub(r"\s+", "", n.upper())
    g = None
    if "MC25" in n2: g = "MC25"
    elif re.search(r"PCMSR\s*(\d\d)", n2): g = "PC" + re.search(r"PCMSR\s*(\d\d)", n2).group(1)
    elif re.search(r"PCBBFS\s*(\d\d)", n2): g = "PCB" + re.search(r"PCBBFS\s*(\d\d)", n2).group(1)
    elif re.search(r"PCB\s*(\d\d)", n2): g = "PCB" + re.search(r"PCB\s*(\d\d)", n2).group(1)
    elif re.search(r"PC\s*(\d\d)", n2): g = "PC" + re.search(r"PC\s*(\d\d)", n2).group(1)
    if not g: return None
    mod = ""
    if re.search(r"ben sun ?f?phat|ben sunfat|PCMSR|-?MS\b|-?HS\b", n + " " + n2, re.I) or re.search(r"(MS|HS)$|(MS|HS)[^A-Z]", n2): mod = " bền sunfat"
    elif re.search(r"xi lo cao|PCBBFS", n + " " + n2, re.I): mod = " xỉ lò cao"
    pk = "bao" if re.search(r"\bbao\b", " ".join((n, u, q))) else ("rời" if re.search(r"\b(roi|xa)\b", " ".join((n, q))) else None)
    if not pk: return None
    return f"Xi măng {g}{mod} {pk}"

def cement_price(r):
    p = next((x for x in r["prices"] if x), None)
    if not p: return None
    u = ascii_(r["unit"] + " " + r["spec"])
    if re.search(r"/\s*bao", ascii_(r["unit"])):  # giá theo bao -> đ/tấn
        kg = re.search(r"(\d\d)\s*kg", u); kg = int(kg.group(1)) if kg else 50
        p = round(p * 1000 / kg)
    return p if 500_000 < p < 5_000_000 else None

BRICK_TYPES = [("tự chèn", r"tu chen"), ("trồng cỏ", r"trong co"), ("block", r"block"), ("ống", r"\bong\b|rong \d lo"),
               ("đinh", r"\bdinh\b"), ("đặc", r"\bdac\b")]
def brick_key(r):
    n = ascii_(r["name"]); size = re.search(r"(\d{2,3})\s*x\s*(\d{2,3})\s*x\s*(\d{2,3})", ascii_(r["name"] + " " + r["spec"]))
    t = next((v for v, pat in BRICK_TYPES if re.search(pat, n)), None)
    return f"Gạch {t} {size.group(1)}x{size.group(2)}x{size.group(3)} mm" if t and size else None

def stone_sand_key(r, cat):
    """Tên chuẩn hoá cho cát/đá. Mục bình quân: giữ nguyên tên Sở công bố."""
    sec = ascii_(r["section"] or "")
    suffix = " – giá bình quân khu vực" if "binh quan" in sec else (" – giá tại mỏ" if "tai mo" in sec else None)
    if not suffix: return None
    name = re.sub(r"\s+", " ", nfc(r["name"])).strip()
    if cat == "cat": return name[0].upper() + name[1:] + suffix
    if "binh quan" in sec: return name + suffix
    n = ascii_(name).replace("*", "x")
    n = re.sub(r"(\d)\s*x\s*(\d)", r"\1x\2", n)
    if re.search(r"phong hoa|loai [45]\b", n): return None  # đá phong hoá / loại 4–5: không dùng cho bê tông, bỏ khỏi khoảng giá
    if re.search(r"^(cap phoi da dam|da dmax)\b", n) and "dmax" in n:  # 'Đá Dmax 37,5' = cấp phối đá dăm Dmax 37,5 (TCVN 8859)
        d = re.search(r"dmax\s*=?\s*(?:0x)?0?(\d+(?:[.,]\d)?)", n)
        v = d.group(1).replace(".", ",") if d else None
        v = {"375": "37,5"}.get(v, v)
        return f"Cấp phối đá dăm Dmax {v}{suffix}" if v in ("25", "37,5") else None
    for pat, nm in ((r"^da 1x2\b|^da 10x20\b", "Đá 1x2"), (r"^da 1x1\b", "Đá 1x1"), (r"^da 0x4\b", "Đá 0x4"),
                    (r"^da 2x4\b|^da 20x40\b", "Đá 2x4"), (r"^da 4x6\b|^da 40x60\b", "Đá 4x6"), (r"^da hoc\b", "Đá hộc"),
                    (r"^da mi sang\b", "Đá mi sàng"), (r"^da mi bui\b", "Đá mi bụi")):
        if re.search(pat, n): return nm + suffix
    return None

def aggregate(kind, rows):
    groups = {}
    for r in rows:
        if kind == "xi_mang": k, p = cement_key(r), cement_price(r)
        elif kind == "gach": k, p = brick_key(r), next((x for x in r["prices"] if x), None)
        else: k, p = stone_sand_key(r, kind), next((x for x in r["prices"] if x), None)
        if k and p: groups.setdefault(k, []).append(p)
    return {k: (min(v), max(v), len(v)) for k, v in groups.items()}

# ---------------- phụ lục bổ sung: thép / cáp điện / bê tông thương phẩm / vữa ----------------
def mill_name(sup):
    a = ascii_(sup)
    for pat, nm in ((r"mien nam|vnsteel", "Thép Miền Nam (VNSteel)"), (r"kyoei", "Vina Kyoei"), (r"pomina", "Pomina"), (r"hoa phat", "Hòa Phát"),
                    (r"tung ?ho", "TungHo"), (r"viet nhat|vina ?japan", "Việt Nhật"), (r"\bvas\b|viet my", "VAS"), (r"posco", "Posco"),
                    (r"viet duc", "Việt Đức"), (r"viet y\b", "Việt Ý"), (r"thai nguyen|tisco", "Thái Nguyên"),
                    (r"cadivi|day cap dien viet nam", "CADIVI"), (r"cadisun", "CADISUN"), (r"tran phu", "Trần Phú"), (r"ls[- ]?vina", "LS-VINA"),
                    (r"viet han", "Việt Hàn"), (r"hodeco", "HODECO")):
        if re.search(pat, a): return nm
    s2 = re.sub(r"^(C[ôo]ng\s*ty|Cty)\s+(TNHH|C[ổo]\s*ph[ầa]n|CP)?\s*(MTV|M[ộo]t\s+Th[àa]nh\s+Vi[êe]n)?\s*", "", sup, flags=re.I).strip()
    return ("Nhà máy vữa Sài Gòn" if s2.lower().startswith("nhà máy") else s2[:48]) or "?"
def steel_key(r):
    """-> (key, label, VND/kg) cho thép cuộn/thanh vằn; bỏ thép góc, tròn trơn, gân ren, cán kéo/không logo."""
    n = ascii_(r["name"]); full = ascii_(" ".join((r["name"], r.get("std") or "", r["spec"])))
    if re.search(r"goc|tron tron|gan ren|can keo|khong logo|\bhinh\b|\btam\b", n): return None
    coil = "cuon" in n
    if not coil and "van" not in n: return None
    d = [int(x) for x in re.findall(r"(?:\bd|ф|ø|phi)\s*(\d{1,2})(?![\d,.])", r["name"].lower().replace("ф", "ф")) + re.findall(r"(\d{1,2})\s*(?:,0\s*)?mm", r["name"])]
    m = re.search(r"\bd\s*(\d{1,2})\s*-\s*d?\s*(\d{1,2})\b", n)
    if m: d += [int(m.group(1)), int(m.group(2))]
    if not d: d = [int(x) for x in re.findall(r"[фø]\s*(\d{1,2})", r["name"].lower())]
    if not d: return None
    lo, hi = min(d), max(d)
    g = re.search(r"\b(cb\s*\d{3})\s*-?\s*([tv])?\b|\b(sd\s*\d{3})\b", full)
    grade = (g.group(1).replace(" ", "").upper() + ("-" + g.group(2).upper() if g.group(2) else "")) if g and g.group(1) else (g.group(3).replace(" ", "").upper() if g else "")
    if coil: prod = f"cuộn D{lo}" if lo == hi else f"cuộn D{lo}–D{hi}"
    else: prod = f"thanh vằn D{lo}" if lo == hi else f"thanh vằn D{lo}–D{hi}"
    mill = mill_name(r["supplier"])
    p = next((x for x in r["prices"] if x), None)
    if not p: return None
    if "tan" in ascii_(r["unit"]): p = p / 1000
    if not 8_000 < p < 40_000: return None
    return f"{mill}|{prod}|{grade}", f"Thép {prod}{' ' + grade if grade else ''} – {mill}", p

CABLE_KEEP = r"^(cv-(50|240)|cvv-(25|50|95|150)|cvv-4x(16|50|120)|cvv-3x95\+1x50|cv/fr-1x240|cxv/se-dsta-3x400|av-120)$"
def cable_key(r):
    code = re.split(r"\s*[–-]\s*(?:\d+[,.]?\d*/\d+|\d+/\d+)", r["spec"])[0]
    code = re.sub(r"\s*\(.*?\)", "", code); code = re.sub(r"\s+", "", code).rstrip("-–")
    if not re.match(CABLE_KEEP, code.lower()): return None
    p = next((x for x in r["prices"] if x), None)
    if not p: return None
    volt = re.search(r"(0,6/1\s*kV|300/500\s*V|12/20\(24\)\s*kV)", r["spec"])
    return code.lower(), f"Cáp {code}{' ' + volt.group(1).replace(' ', '') if volt else ''} – {mill_name(r['supplier'])}", p

def rmc_key(r):
    m = re.search(r"\bm\s*(\d{3})\b", ascii_(r["name"]))
    p = next((x for x in r["prices"] if x), None)
    if not m or not p or not 500_000 < p < 5_000_000: return None
    return f"m{m.group(1)}", f"Bê tông thương phẩm M{m.group(1)}", p

def mortar_key(r):
    p = next((x for x in r["prices"] if x), None)
    if not p: return None
    nm = re.sub(r"\s+", " ", nfc(r["name"])).strip()
    return slug(nm), nm, p

def aggregate_extra(kind, rows):
    """-> {key: [lo, hi, n, label, suppliers]}"""
    fn = {"thep": steel_key, "cap": cable_key, "be_tong": rmc_key, "vua": mortar_key}[kind]; g = {}
    for r in rows:
        k = fn(r)
        if not k: continue
        key, label, p = k; e = g.setdefault(key, [p, p, 0, label, []])
        e[0], e[1], e[2] = min(e[0], p), max(e[1], p), e[2] + 1
        sup = mill_name(r["supplier"])
        if sup not in e[4]: e[4].append(sup)
    return g
XCAT = {"thep": ("Thép xây dựng", "VND/kg", "thep"), "cap": ("Cáp điện (MEP)", "VND/m", "cap"),
        "be_tong": ("Bê tông thương phẩm", "VND/m³", "rmc"), "vua": ("Vữa & hoàn thiện", "VND/bao", "vua")}

def parse_extra(c):
    """Bổ sung c['series'] (thép/cáp/bê tông/vữa) cho một thông báo đã cache; tải lại Drive nếu thiếu."""
    have = c.get("series") or {}
    if all(k in have for k in EXTRA): return False
    files = drive_files(c["drive"])
    pri = [f for f in files if re.search(r"thep|cap|day dien|be tong thuong|vua", ascii_(f[1]))]
    rest = [f for f in files if f not in pri and not re.search(r"xi ?mang|gach|\bda\b|\bcat\b|thong bao", ascii_(f[1]))]
    done = dict(have)
    for did, name in pri + rest:
        if all(k in done for k in EXTRA): break
        try: kind, title, rows = table_rows(drive_pdf(did))
        except Exception as e: print("hcm_sxd extra", name, e, file=sys.stderr); continue
        if kind in EXTRA and kind not in done:
            done[kind] = aggregate_extra(kind, rows)
            c.setdefault("appendices", {})[kind] = {"file": name, "drive_id": did, "n_rows": len(rows)}
    for k in EXTRA: done.setdefault(k, {})  # không có phụ lục tháng đó -> rỗng, không thử lại mãi
    c["series"] = done; return True

def extra_items(c, prev, hist):
    out = []; m, y = int(c["month"][5:]), c["month"][:4]
    tb = f"TB {c['tb']}/TB-SXD-KTVLXD" if c.get("tb") else "TB công bố giá"
    for kind, g in (c.get("series") or {}).items():
        cat, unit, pre = XCAT[kind]
        for key, (lo, hi, n, label, sups) in sorted(g.items()):
            iid = f"sxd_hcm_{pre}_" + slug(key)
            pv = ((prev or {}).get("series") or {}).get(kind, {}).get(key)
            pct = round((lo / pv[0] - 1) * 100, 2) if pv and pv[0] else None
            note = f"Sở XD TP.HCM công bố giá tháng {m}/{y} ({tb}); giá NSX/NCC kê khai, chưa VAT"
            if kind == "be_tong": note += f"; khoảng thấp–cao giữa {n} NCC: {', '.join(sups[:6])}; độ sụt/điều kiện giao theo từng NCC"
            elif n > 1: note += f"; khoảng thấp–cao giữa {n} dòng giá"
            bf = [(h.get("issued") or h["month"] + "-28", h["series"][kind][key][0]) for h in hist
                  if h is not c and key in ((h.get("series") or {}).get(kind) or {})]
            out.append(dict(id=iid, grp="vn", category=cat, name=label + (" (Sở XD TP.HCM)" if kind != "be_tong" else " – các NCC (Sở XD TP.HCM)"),
                            unit=unit, currency="VND", price=lo, price_high=hi if hi != lo else None,
                            src=f"Sở Xây dựng TP.HCM – công bố giá tháng {m}/{y}", url=c.get("drive") or c.get("article"),
                            as_of=c.get("issued") or f"{c['month']}-28", region=REGION, change_pct=pct, note=note,
                            brand=sups[0] if len(sups) == 1 else None, backfill=bf))
    return out

CAT = {"xi_mang": ("Xi măng", "VND/tấn"), "gach": ("Gạch xây", "VND/viên"), "da": ("Đá xây dựng", "VND/m³"), "cat": ("Cát", "VND/m³")}

def parse_notice(notice):
    """Download + parse one monthly notice -> cache dict."""
    files = drive_files(notice["drive"]); appx = {}
    pri = [f for f in files if re.search(r"xi ?mang|gach|\bda\b|\bcat\b", ascii_(f[1]))]
    for did, name in pri + [f for f in files if f not in pri]:
        if len(appx) == len(KINDS): break
        if re.search(r"thong bao|^\d{4,6}[- ]", ascii_(name)) and "phu luc" not in ascii_(name): continue
        kind, title, rows = table_rows(drive_pdf(did))
        if kind in KINDS and kind not in appx: appx[kind] = {"file": name, "drive_id": did, "rows": rows}
    miss = [k for k in KINDS if k not in appx]
    if miss: raise RuntimeError(f"thiếu phụ lục: {miss}")
    groups = {k: {n: list(v) for n, v in aggregate(k, a["rows"]).items()} for k, a in appx.items()}
    return {"month": notice["month"], "tb": notice.get("tb"), "issued": notice.get("issued"), "article": notice["article"],
            "pdf": notice.get("pdf"), "drive": notice["drive"], "parsed_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "appendices": {k: {"file": a["file"], "drive_id": a["drive_id"], "n_rows": len(a["rows"])} for k, a in appx.items()},
            "groups": groups}

def items_from_cache(c, prev=None):
    out = []; m, y = int(c["month"][5:]), c["month"][:4]
    tb = f"TB {c['tb']}/TB-SXD-KTVLXD" if c.get("tb") else "TB công bố giá"
    for kind, g in c["groups"].items():
        cat, unit = CAT[kind]
        for name, (lo, hi, n) in sorted(g.items()):
            iid = "vnmat_" + slug(cat + " " + name)
            pct = None
            if prev and "giá tại mỏ" not in name:  # khoảng giữa các mỏ: đầu thấp đổi theo mỏ nào báo giá trong tháng -> không tính %
                pv = prev["groups"].get(kind, {}).get(name)
                if pv and pv[0]: pct = round((lo / pv[0] - 1) * 100, 2)
            note = f"Sở XD TP.HCM công bố giá tháng {m}/{y} ({tb}); chưa VAT"
            note += "; khoảng thấp–cao giữa " + (f"{n} NCC" if kind in ("xi_mang", "gach") else f"{n} dòng giá tại mỏ") if n > 1 else ""
            out.append(dict(id=iid, grp="vn", category=cat, name=name, unit=unit, currency="VND", price=lo,
                            price_high=hi if hi != lo else None, src=f"Sở Xây dựng TP.HCM – công bố giá tháng {m}/{y}",
                            url=c.get("drive") or c.get("article"), as_of=c.get("issued") or f"{c['month']}-28",
                            region=REGION, change_pct=pct, note=note))
    return out

def src_hcm_sxd():
    """fetcher source: newest parsed notice (download only if not cached)."""
    os.makedirs(CACHE, exist_ok=True); errs = []
    try:
        for n in latest_notices(NBACK):
            p = os.path.join(CACHE, n["month"] + ".json")
            if not os.path.exists(p):
                try:
                    c = parse_notice(n); json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                    print("hcm_sxd: parsed", n["month"], c.get("tb"), {k: len(v) for k, v in c["groups"].items()}, file=sys.stderr)
                except Exception as e: errs.append(f"{n['month']}: {e}")
    except Exception as e: errs.append(f"discover: {e}")
    if errs: print("hcm_sxd errors", errs, file=sys.stderr)
    months = sorted(f[:-5] for f in os.listdir(CACHE) if re.fullmatch(r"\d{4}-\d\d\.json", f))
    if not months: raise RuntimeError("; ".join(errs) or "chưa có thông báo nào")
    hist = [json.load(open(os.path.join(CACHE, k + ".json"), encoding="utf-8")) for k in months[-NBACK:]]
    for k, c in zip(months[-NBACK:], hist):  # thép/cáp/bê tông/vữa: bổ sung vào cache cũ (một lần cho mỗi tháng)
        try:
            if parse_extra(c):
                json.dump(c, open(os.path.join(CACHE, k + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print("hcm_sxd: extra", k, {x: len(v) for x, v in c["series"].items()}, file=sys.stderr)
        except Exception as e: errs.append(f"extra {k}: {e}"); print("hcm_sxd extra error", k, e, file=sys.stderr)
    cur, prev = hist[-1], (hist[-2] if len(hist) > 1 else None)
    return items_from_cache(cur, prev) + extra_items(cur, prev, hist)

if __name__ == "__main__":
    for r in src_hcm_sxd(): print(r["id"], r["price"], r.get("price_high"), r["unit"], r["as_of"], r.get("change_pct"))
