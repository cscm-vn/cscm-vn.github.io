"""Nguồn giá giao ngay BỔ SUNG cho fetcher.py: bê tông thương phẩm (M250/M300, HN & HCM), nhựa (PE/PVC/PP – TE),
ống HDPE Tiền Phong. Trả về dict cùng định dạng fetcher.item(). Không bịa giá: lỗi parse => raise, fetcher giữ giá cũ."""
import re, io, html, unicodedata, datetime as dt
from zoneinfo import ZoneInfo
import requests, pandas as pd

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept-Language": "vi,en;q=0.8"}
TODAY = dt.datetime.now(ZoneInfo("Asia/Saigon")).date().isoformat()

def _get(u):
    try:
        r = requests.get(u, headers=UA, timeout=30); r.raise_for_status(); return r.text
    except requests.exceptions.SSLError:  # một số site VN lỗi TLS với requests -> dùng curl
        import subprocess
        return subprocess.run(["curl", "-sL", "-m", "30", "-A", UA["User-Agent"], u], capture_output=True, text=True, check=True).stdout
def _vnf(v): return f"{v:,.0f}".replace(",", ".")  # Vietnamese thousands separator
def _vn(s):  # '1.430.000' / '1650.000' -> 1430000
    s = re.sub(r"[^\d]", "", str(s)); return float(s) if s else None
def _it(id, cat, name, unit, cur, price, src, url, region=None, grp="vn", **kw):
    d = dict(id=id, grp=grp, category=cat, name=name, unit=unit, currency=cur, price=price, src=src, url=url,
             as_of=TODAY, region=region); d.update(kw); return d

GRADES = tuple(str(g) for g in (100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700))  # mác dùng trong HĐ tổng thầu
def _concrete_table(url, src, prefix, region, grades=GRADES):
    t = pd.read_html(io.StringIO(_get(url)))[0]
    out = []
    for _, r in t.iterrows():
        name = str(r.iloc[1])
        for g in grades:
            if re.search(rf"^\D{{0,6}}{g}\b", unicodedata.normalize("NFC", name)):
                lo, hi = _vn(r.iloc[3]), _vn(r.iloc[4])
                if not lo or not (500_000 < lo < 5_000_000): continue
                out.append(_it(f"{prefix}_m{g}", "Bê tông thương phẩm", f"Bê tông tươi M{g} đá 1x2, sụt 12±2 ({src})",
                               "VND/m³", "VND", lo, src, url, region, price_high=hi,
                               note=f"Cát thường {_vnf(lo)} – cát vàng {_vnf(hi)} đ/m³; chưa VAT, gồm vận chuyển nội thành; báo giá NCC"))
    if not out: raise RuntimeError(f"{src}: không thấy dòng M250/M300")
    return out

def src_concrete():
    out, errs = [], []
    for args in [("https://betonghanoi.com.vn/", "betonghanoi.com.vn", "rmc_hn_btHN", "Hà Nội"),
                 ("https://betongtuoichem.com/", "betongtuoichem.com", "rmc_hn_chem", "Hà Nội")]:
        try: out += _concrete_table(*args)
        except Exception as e: errs.append(str(e))
    try:  # TP.HCM: bảng 2 cột 'Mác | lo ~ hi'
        u = "https://betongdvc.com/bao-gia-be-tong-tuoi-tp-hcm/"
        t = pd.read_html(io.StringIO(_get(u)))[0]
        for _, r in t.iterrows():
            g = re.sub(r"\D", "", str(r.iloc[0]))
            if g in GRADES:
                lo, hi = [_vn(x) for x in str(r.iloc[1]).split("~")]
                out.append(_it(f"rmc_hcm_dvc_m{g}", "Bê tông thương phẩm", f"Bê tông tươi M{g} đá 1x2 (betongdvc.com)",
                               "VND/m³", "VND", lo, "betongdvc.com", u, "TP.HCM", price_high=hi,
                               note=f"Khoảng {_vnf(lo)} – {_vnf(hi)} đ/m³; báo giá NCC tham khảo"))
    except Exception as e: errs.append(f"dvc: {e}")
    if errs: print("concrete partial errors:", errs)
    if not out: raise RuntimeError("; ".join(errs))
    return out

TE_PLASTIC = {"polyethylene": ("te_polyethylene", "Polyethylene (PE, DCE LLDPE)"),
              "polyvinyl": ("te_pvc", "PVC (Polyvinyl chloride, DCE)"),
              "polypropylene": ("te_polypropylene", "Polypropylene (PP, DCE)")}
def te_desc(slug):
    t = _get(f"https://tradingeconomics.com/commodity/{slug}")
    m = re.search(r'name="description" content="([^"]*)"', t) or re.search(r'content="([^"]*)" name="description"', t)
    return html.unescape(m.group(1)) if m else ""
def parse_te_desc(d):
    """'X rose to 8,646 CNY/T on October 21, 2026 ... past month ... risen 4.98%, ... up 25.16% compared to ... last year'"""
    m = re.search(r"to ([\d,\.]+) ([A-Z]{3})/(\w+) on ([A-Za-z]+ \d+, \d{4})", d)
    if not m: return None
    p = float(m.group(1).replace(",", ""))
    mo = re.search(r"past month[^%]*?(risen|fallen|increased|decreased|gained|lost)\s*([\d\.]+)%", d)
    yr = re.search(r"(up|down)\s*([\d\.]+)% compared to the same time last year|([\d\.]+)% (higher|lower) than a year ago", d)
    ch1m = None if not mo else float(mo.group(2)) * (1 if mo.group(1) in ("risen", "increased", "gained") else -1)
    ch1y = None
    if yr:
        if yr.group(1): ch1y = float(yr.group(2)) * (1 if yr.group(1) == "up" else -1)
        else: ch1y = float(yr.group(3)) * (1 if yr.group(4) == "higher" else -1)
    as_of = dt.datetime.strptime(m.group(4), "%B %d, %Y").date().isoformat()
    return dict(price=p, cur=m.group(2), unit=m.group(3), ch1m=ch1m, ch1y=ch1y, as_of=as_of)

def src_plastics():
    out = []
    for slug, (id, name) in TE_PLASTIC.items():
        try:
            x = parse_te_desc(te_desc(slug))
            if not x: continue
            out.append(_it(id, "Nhựa (nguyên liệu)", name, f"{x['cur']}/tấn", x["cur"], x["price"], "Trading Economics",
                           f"https://tradingeconomics.com/commodity/{slug}", grp="world", as_of=x["as_of"],
                           note=f"1 tháng {x['ch1m']:+.1f}% · 1 năm {x['ch1y']:+.1f}% (TE)" if x["ch1m"] is not None and x["ch1y"] is not None else None))
        except Exception: pass
    if not out: raise RuntimeError("TE plastics parse failed")
    return out

def src_hdpe_pipe():
    u = "https://ongnuoctienphong.vn/bang-bao-gia-ong-nhua-va-phu-kien-hdpe-tien-phong-2021/"
    ts = pd.read_html(io.StringIO(_get(u))); out = []
    for t in ts:
        for _, r in t.iterrows():
            nm = str(r.iloc[1]); pn = str(r.iloc[3])
            for d in ("110", "63"):
                if re.search(rf"PE 100 – Phi {d}$", nm) and pn in ("10", "10.0"):
                    p = _vn(r.iloc[5])
                    out.append(_it(f"pipe_hdpe_pe100_d{d}_pn10", "Ống nhựa (MEP)", f"Ống HDPE PE100 Ø{d} PN10 Tiền Phong",
                                   "VND/m", "VND", p, "ongnuoctienphong.vn (đại lý Tiền Phong)", u, "Miền Nam",
                                   note="Giá chưa VAT theo bảng giá đại lý; chiết khấu dự án thường 20–40%"))
    if not out: raise RuntimeError("HDPE table parse failed")
    return out

def _rmc_grade_table(url, src, prefix, region, note, vat=False):
    """Bảng giá kiểu 'M400R28 … đơn giá' (cột cuối là giá) – lấy bảng đầu tiên có dòng M400."""
    out = []
    for t in pd.read_html(io.StringIO(_get(url))):
        for _, r in t.iterrows():
            cells = [str(c) for c in r.tolist()]
            m = re.search(r"M(?:ác)?\s*(\d{3})\s*R?28", " ".join(cells[:3]), re.I)
            if not m or m.group(1) not in GRADES: continue
            nums = [_vn(c) for c in cells if re.fullmatch(r"[\d.]{7,9}", c.strip())]
            p = next((v for v in reversed(nums) if v and 500_000 < v < 5_000_000), None)
            if p and f"{prefix}_m{m.group(1)}" not in {o["id"] for o in out}:
                out.append(_it(f"{prefix}_m{m.group(1)}", "Bê tông thương phẩm", f"Bê tông tươi M{m.group(1)} đá 1x2, sụt 10±2 ({src})",
                               "VND/m³", "VND", p, src, url, region, note=note))
        if any(o["id"].endswith("m400") for o in out): break
    if not out: raise RuntimeError(f"{src}: không thấy bảng mác bê tông")
    return out

def src_concrete_hcm2():
    out, errs = [], []
    for args in [("https://betongdongnam.com/cap-nhat-gia-be-tong-tuoi-tphcm-nhanh/", "betongdongnam.com", "rmc_hcm_dn", "TP.HCM",
                  "Báo giá NCC tham khảo (bảng chung TP.HCM), chưa gồm bơm; VAT theo NCC"),
                 ("https://mekongthuongtin.com/gia-be-tong-tuoi/", "mekongthuongtin.com", "rmc_hcm_mk", "TP.HCM",
                  "Báo giá NCC tham khảo, ĐÃ gồm VAT 8%, chưa gồm bơm")]:
        try: out += _rmc_grade_table(*args)
        except Exception as e: errs.append(str(e))
    if errs: print("concrete HCM2 partial errors:", errs)
    if not out: raise RuntimeError("; ".join(errs))
    return out

def _tables(url):
    return pd.read_html(io.StringIO(_get(url)))
def _cells(r): return [unicodedata.normalize("NFC", str(c)) for c in r.tolist()]
def _range(s):  # '1.350.000 – 1.540.000' / '1.800-2.100' -> (lo, hi)
    ps = [_vn(x) for x in re.split(r"\s*[–~-]\s*", str(s)) if re.search(r"\d", x)]
    return (ps[0], ps[-1]) if ps else (None, None)

def src_contract_materials():
    """Vật tư theo dõi Điều chỉnh giá HĐ tổng thầu: gạch AAC, vữa khô/skimcoat, Sika Latex TH, gạch đặc, hệ trần thạch cao.
    Bảng giá đại lý/nhà máy công khai (cập nhật không định kỳ – giá giữ nguyên nhiều tuần là bình thường). Lỗi từng nguồn bỏ qua."""
    out, errs = [], []
    def add(*a, **k): out.append(_it(*a, **k))
    try:  # 1) AAC Viglacera – đại lý Hà Nội (khoảng giá đ/m³)
        u = "https://betongsieunhe.vn/gach-aac-viglacera/"
        for t in _tables(u):
            for _, r in t.iterrows():
                c = _cells(r); size = re.sub(r"\s", "", c[2]) if len(c) > 3 else ""
                for d, tag in (("100", "≥100"), ("75", "<100")):
                    if size == f"600×200×{d}":
                        lo, hi = _range(c[3])
                        if lo and 800_000 < lo < 4_000_000:
                            add(f"aac_hn_viglacera_d{d}", "Gạch xây", f"Gạch AAC Viglacera 600×200×{d} (tường {tag} mm) – đại lý HN", "VND/m³", "VND", lo,
                                "betongsieunhe.vn (đại lý Viglacera HN)", u, "Hà Nội", price_high=hi, note=f"Khoảng {_vnf(lo)} – {_vnf(hi)} đ/m³, giá tham khảo đại lý")
    except Exception as e: errs.append(f"AAC HN: {e}")
    try:  # 2) EBLOCK – bảng giá niêm yết nhà máy (miền Nam) + phụ kiện
        u = "https://eblock.com.vn/bao-gia-gach-be-tong-khi-chung-ap-aac-eblock-2025/"
        ts = _tables(u)
        for _, r in ts[0].iterrows():
            c = _cells(r)
            for d, tag in (("100", "≥100"), ("75", "<100")):
                if c[0].strip() == "EBLOCK 3.5" and re.sub(r"\s", "", c[2]) == f"600×200×{d}":
                    p = _vn(c[4])
                    if p and 800_000 < p < 4_000_000:
                        add(f"aac_hcm_eblock_b3_d{d}", "Gạch xây", f"Gạch AAC EBLOCK B3 600×200×{d} (tường {tag} mm) – giá nhà máy", "VND/m³", "VND", p,
                            "eblock.com.vn (niêm yết nhà máy)", u, "TP.HCM", note="Giá niêm yết nhà máy, chưa VAT & vận chuyển")
        for t in ts:
            for _, r in t.iterrows():
                c = _cells(r)
                if len(c) < 4: continue
                kg = re.search(r"Bao\s*(\d+)\s*kg", c[1]); p = _vn(c[3].split("/")[0])
                if not p: continue
                if c[0].startswith("Vữa xây mỏng EBS") and kg:
                    add("mortar_aac_eblock_ebs301", "Vữa & hoàn thiện", "Vữa xây gạch AAC EBLOCK EBS 301 (quy đ/kg)", "VND/kg", "VND", round(p / int(kg.group(1))),
                        "eblock.com.vn (niêm yết nhà máy)", u, "TP.HCM", note=f"{_vnf(p)} đ/bao {kg.group(1)} kg")
                elif c[0].startswith("Vữa tô mỏng Skimcoat") and kg:
                    add("skimcoat_eblock_ebs302", "Vữa & hoàn thiện", "Skimcoat EBLOCK EBS 302 (quy đ/kg)", "VND/kg", "VND", round(p / int(kg.group(1))),
                        "eblock.com.vn (niêm yết nhà máy)", u, "TP.HCM", note=f"{_vnf(p)} đ/bao {kg.group(1)} kg")
                elif c[0].startswith("Lưới sợi thủy tinh"):
                    m = re.search(r"1m\s*×\s*(\d+)m", c[1])
                    if m: add("mesh_fiberglass_eblock", "Vữa & hoàn thiện", "Lưới sợi thủy tinh chống nứt (vật tư, quy đ/m)", "VND/m", "VND", round(p / int(m.group(1))),
                              "eblock.com.vn (niêm yết nhà máy)", u, "TP.HCM", note=f"{_vnf(p)} đ/cuộn 1m×{m.group(1)}m – chỉ vật tư")
    except Exception as e: errs.append(f"EBLOCK: {e}")
    try:  # 3) Vữa khô / skimcoat – tổng kho Hà Nội
        u = "https://gachbetongnhe.com.vn/bao-gia-vua-kho-tron-san/"
        M = {"Vữa xây gạch AAC Mater M75": ("mortar_aac_mater_m75", "Vữa xây gạch AAC Mater M75 (quy đ/kg)"),
             "Vữa Sako M75 S900": ("mortar_aac_sako_m75_s900", "Vữa xây AAC Sako M75 S900 (quy đ/kg)"),
             "Bột bả Skimcoat 401 Mater": ("skimcoat_mater_401", "Skimcoat Mater 401 (quy đ/kg)")}
        for t in _tables(u):
            for _, r in t.iterrows():
                c = _cells(r)
                if c[0].strip() in M:
                    kg = re.search(r"(\d+)\s*kg", c[1]); p = _vn(c[2])
                    if kg and p:
                        i, nm = M[c[0].strip()]
                        add(i, "Vữa & hoàn thiện", nm, "VND/kg", "VND", round(p / int(kg.group(1))), "gachbetongnhe.com.vn (tổng kho HN)", u, "Hà Nội",
                            note=f"{_vnf(p)} đ/bao {kg.group(1)} kg")
    except Exception as e: errs.append(f"vữa khô HN: {e}")
    try:  # 4) Sika Latex TH – báo giá đại lý Sika (TP.HCM)
        u = "https://hoachatxaydung.vn/blogs/news/bao-gia-sika-nam-2026"
        for t in _tables(u):
            for _, r in t.iterrows():
                c = _cells(r)
                if len(c) > 3 and re.fullmatch(r"Sika Latex TH\s*-\s*25L", c[1].strip()):
                    p = _vn(c[3])
                    if p and 20_000 < p < 200_000:
                        add("sika_latex_th_25l", "Vữa & hoàn thiện", "Sika Latex TH can 25 L (đ/lít)", "VND/lít", "VND", p, "hoachatxaydung.vn (đại lý Sika Chính Tiến)", u, "TP.HCM",
                            note="Đơn giá đề nghị theo lít, chưa VAT & vận chuyển; báo giá năm 2026 của đại lý")
    except Exception as e: errs.append(f"Sika: {e}")
    try:  # 5) Gạch đặc A1 205×95×55 – bảng tham khảo theo khu vực
        u = "https://anx.vn/gia-gach-xay-nha.html"
        for t in _tables(u):
            for _, r in t.iterrows():
                c = _cells(r)
                if len(c) >= 4 and c[0].strip() == "Gạch đặc A1" and c[1].strip() == "205x95x55" and "Hà Nội" in c[3]:
                    lo, hi = _range(c[2])
                    if lo and 500 < lo < 10_000:
                        add("brick_solid_a1_205x95x55_hn", "Gạch xây", "Gạch đặc A1 205×95×55 – Hà Nội (giá tham khảo)", "VND/viên", "VND", lo, "anx.vn (bảng giá tham khảo)", u, "Hà Nội",
                            price_high=hi, note=f"Khoảng {_vnf(lo)} – {_vnf(hi)} đ/viên")
    except Exception as e: errs.append(f"gạch: {e}")
    try:  # 6) Hệ trần thạch cao Vĩnh Tường (tấm + khung Tika) – giá tham khảo hãng
        u = "https://vinhtuong.com/gia-tam-thach-cao"
        for t in _tables(u):
            for _, r in t.iterrows():
                c = _cells(r)
                if len(c) < 2 or "Tika" not in c[0]: continue
                m_ = re.match(r"([\d.]+)\s*VNĐ", c[1].strip()); p = _vn(m_.group(1)) if m_ else None
                if not p: continue
                if c[0].startswith("Tấm Vĩnh Tường Tiêu chuẩn"):
                    add("ceiling_vinhtuong_std_tika", "Vữa & hoàn thiện", "Trần thạch cao Vĩnh Tường tấm tiêu chuẩn + khung Tika (giá hãng)", "VND/m²", "VND", p, "vinhtuong.com (giá tham khảo hãng)", u, None,
                        note="Giá hệ trần tham khảo trên website hãng (tấm + khung); điều kiện thi công không công bố")
                elif c[0].startswith("Tấm thạch cao Vĩnh Tường Siêu chịu ẩm") and "chống mốc" not in c[0]:
                    add("ceiling_vinhtuong_mr_tika", "Vữa & hoàn thiện", "Trần thạch cao Vĩnh Tường tấm siêu chịu ẩm + khung Tika (giá hãng)", "VND/m²", "VND", p, "vinhtuong.com (giá tham khảo hãng)", u, None,
                        note="Giá hệ trần tham khảo trên website hãng (tấm + khung); điều kiện thi công không công bố")
    except Exception as e: errs.append(f"Vĩnh Tường: {e}")
    if errs: print("contract materials partial errors:", errs)
    if not out: raise RuntimeError("; ".join(errs) or "không có dòng nào")
    return out

NEW_SOURCES = [("Bê tông thương phẩm (NCC)", src_concrete), ("Bê tông TP.HCM mác cao (NCC)", src_concrete_hcm2), ("Nhựa PE/PVC/PP (TE)", src_plastics),
               ("Ống HDPE Tiền Phong", src_hdpe_pipe), ("Vật tư HĐ tổng thầu (AAC, vữa, Sika, gạch, trần)", src_contract_materials)]

if __name__ == "__main__":
    for n, f in NEW_SOURCES:
        try:
            for r in f(): print(n, "|", r["id"], r["price"], r.get("price_high"), r["unit"], r.get("note"))
        except Exception as e: print("FAIL", n, e)
