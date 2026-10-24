#!/usr/bin/env python3
"""Dựng trends/data/suppliers.json cho bảng 'Tra cứu nhà cung cấp' trên nha-thau.html (hub tĩnh, không gọi API từ trình duyệt).
Chạy THỦ CÔNG (không nằm trong cập nhật hằng ngày):
  python trends/supplier_profiles.py                      # dựng suppliers.json từ seed (kiểm tra phép cộng trừ, tính chỉ số & nhãn)
  python trends/supplier_profiles.py --refresh-registry   # lấy lại thông tin đăng ký theo MST từ VietQR (nguồn: Tổng cục Thuế), ghi seed/suppliers_registry.json
  python trends/supplier_profiles.py --check              # in cảnh báo dữ liệu cũ (> 120 ngày) – KHÔNG tự lấy BCTC
Nguồn & ràng buộc:
  - Đăng ký/tình trạng thuế: VietQR API công khai (https://api.vietqr.io/v2/business/<MST>), dữ liệu tổng hợp từ Tổng cục Thuế. Không dùng masothue.com (cấm tự động hoá).
  - BCTC công ty niêm yết: tải PDF từ trang công bố thông tin của chính công ty, ĐỌC TAY + kiểm phép cộng trừ (seed/suppliers_financials.json). KHÔNG tự động hoá việc lấy BCTC; cập nhật tay mỗi quý.
  - Công ty không niêm yết: chỉ có thông tin đăng ký; không ước lượng doanh thu/lợi nhuận."""
import json, os, re, sys, time, unicodedata, datetime as dt, urllib.request, urllib.error
H = os.path.dirname(os.path.abspath(__file__)); SEED = os.path.join(H, "seed"); DATA = os.path.join(H, "data")
TZ = dt.timezone(dt.timedelta(hours=7)); TODAY = dt.datetime.now(TZ).date()
UNITS_F, FIN_F, REG_F, OUT_F = (os.path.join(SEED, "suppliers_units.json"), os.path.join(SEED, "suppliers_financials.json"),
                                os.path.join(SEED, "suppliers_registry.json"), os.path.join(DATA, "suppliers.json"))
STALE_DAYS = 120   # dữ liệu đã kiểm tra quá N ngày => cảnh báo cần cập nhật
OLD_PERIOD_DAYS = 200  # kỳ báo cáo kết thúc quá N ngày => cảnh báo kỳ cũ
def J(p, d=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return d
def strip(s):
    s = unicodedata.normalize("NFD", (s or "").lower()); return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
def norm_name(s):
    t = strip(s); t = t.replace("&", " va ")
    t = re.sub(r"\(.*?\)", " ", t); t = re.sub(r"[^a-z0-9 ]", " ", t)
    t = re.sub(r"\btrach nhiem huu han\b", "tnhh", t); t = re.sub(r"\bco phan\b", "cp", t); t = re.sub(r"\bcong ty\b", "ct", t)
    return re.sub(r"\s+", " ", t).strip()

# ---------- 1) registry (VietQR) ----------
def vietqr(mst):
    req = urllib.request.Request("https://api.vietqr.io/v2/business/" + mst, headers={"User-Agent": "Mozilla/5.0 (hub-supplier-lookup; manual run)"})
    for k in range(4):
        try:
            return json.load(urllib.request.urlopen(req, timeout=30))
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(6 * (k + 1)); continue
            return {"err": f"HTTP {e.code}"}
        except Exception as e: time.sleep(3)
    return {"err": "timeout"}
def refresh_registry():
    units = J(UNITS_F)["units"]; reg = J(REG_F, {"schema": 1, "records": {}}); rec = reg["records"]; n_ok = 0
    for u in units:
        r = vietqr(u["mst"]); time.sleep(1.5); d = (r or {}).get("data")
        if r.get("code") == "00" and d and d.get("id") == u["mst"]:
            rec[u["mst"]] = dict(legal=d.get("name"), intl=d.get("internationalName"), short=d.get("shortName"), address=d.get("address"), status=d.get("status"),
                fetched=TODAY.isoformat(), upstream_updated=((r.get("metadata") or {}).get("updatedAt") or "")[:10] or None)
            n_ok += 1; print("OK ", u["mst"], d.get("name"), "|", d.get("status"))
        else: print("KEEP (không lấy được, giữ bản cũ)", u["mst"], u["org"], r.get("err") or r.get("desc"))
    reg["records"] = rec; json.dump(reg, open(REG_F, "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True); print(f"registry: {n_ok}/{len(units)} cập nhật")

# ---------- 2) tài chính ----------
def sget(v, k): return v.get(k)
def d_(a): return dt.date.fromisoformat(a)
def check_period(tk, p):
    """Kiểm phép cộng trừ trên số liệu đã nhập – nếu lệch thì dừng build (không xuất số sai)."""
    v = p["v"]; errs = []; tol = 2
    if abs(v["ta"] - (v["liab"] + v["eq"])) > tol: errs.append("Tổng tài sản ≠ Nợ + Vốn chủ")
    if abs(v["rev"] - v["cogs"] - v["gp"]) > tol: errs.append("DT thuần − giá vốn ≠ LN gộp")
    if v["ca"] > v["ta"]: errs.append("TSNH > Tổng TS")
    if v["cl"] > v["liab"]: errs.append("Nợ NH > Tổng nợ")
    if v["debt_st"] + v["debt_lt"] > v["liab"]: errs.append("Nợ vay > Tổng nợ")
    if v["cash"] + v["sti"] > v["ca"]: errs.append("Tiền + ĐTTC NH > TSNH")
    if v["ar"] > v["ca"] or v["inv"] > v["ca"]: errs.append("Phải thu/Tồn kho > TSNH")
    if v["gp"] > v["rev"]: errs.append("LN gộp > DT")
    if errs: raise SystemExit(f"[{tk} {p['id']}] kiểm tra phép tính LỖI: " + "; ".join(errs))
    return ["Tổng tài sản = Nợ phải trả + Vốn chủ sở hữu", "Doanh thu thuần − giá vốn = Lợi nhuận gộp (sai số ≤ 2 đồng)", "Các khoản con nhỏ hơn tổng (TSNH, nợ NH, nợ vay, tiền, phải thu, tồn kho)"]
def metrics(p):
    v = p["v"]; days = (d_(p["end"]) - d_(p["start"])).days + 1; debt = v["debt_st"] + v["debt_lt"]
    return dict(gm=v["gp"] / v["rev"], nm=v["np"] / v["rev"], de=v["liab"] / v["eq"] if v["eq"] > 0 else None, debt=debt,
                dbe=debt / v["eq"] if v["eq"] > 0 else None, cr=v["ca"] / v["cl"], dso=v["ar"] / v["rev"] * days, days=days,
                fin_share=(v["fin_inc"] / v["pbt"]) if v["pbt"] > 0 else None)
RULES = [
 dict(id="lev", name="Nợ vay ÷ vốn chủ sở hữu", short="Mức vay", desc="Vay và nợ thuê tài chính (ngắn + dài hạn) so với vốn chủ. Vay càng nhiều so với vốn tự có thì áp lực lãi vay và rủi ro trả nợ càng lớn.", tiers="> 1,0 lần: +1 điểm · > 2,0 lần: +2 điểm"),
 dict(id="cr", name="Thanh khoản hiện hành (TSNH ÷ nợ ngắn hạn)", short="Thanh khoản", desc="Tài sản ngắn hạn có đủ trả nợ ngắn hạn không. Dưới 1 nghĩa là nợ đến hạn lớn hơn tài sản có thể quy ra tiền trong 12 tháng.", tiers="< 1,2: +1 điểm · < 1,0: +2 điểm"),
 dict(id="cfo", name="Dòng tiền từ hoạt động kinh doanh (CFO)", short="Dòng tiền", desc="Tiền thật thu về từ hoạt động chính. Lãi trên giấy nhưng CFO âm kéo dài là dấu hiệu bị chiếm dụng vốn (phải thu, tồn kho tăng).", tiers="CFO âm kỳ gần nhất: +1 điểm · âm cả kỳ liền trước: +2 điểm"),
 dict(id="nm", name="Biên lợi nhuận ròng (LNST ÷ doanh thu)", short="Lợi nhuận", desc="Lợi nhuận sau thuế trên mỗi đồng doanh thu. Nhà thầu có biên mỏng, thua lỗ thì khả năng chịu cú sốc giá vật tư kém.", tiers="< 1%: +1 điểm · ≤ 0 (lỗ): +2 điểm"),
 dict(id="dso", name="Số ngày thu tiền (phải thu khách hàng ÷ doanh thu × số ngày kỳ)", short="Thu tiền", desc="Trung bình mất bao nhiêu ngày để thu tiền khách. Càng dài càng dễ kẹt vốn và phải kéo dài công nợ với nhà cung cấp.", tiers="> 150 ngày: +1 điểm · > 240 ngày: +2 điểm"),
 dict(id="gr", name="Doanh thu so với kỳ liền trước", short="Doanh thu", desc="Doanh thu giảm mạnh thường kéo theo thiếu việc, khó hấp thụ chi phí cố định.", tiers="giảm > 20%: +1 điểm"),
 dict(id="eq", name="Vốn chủ sở hữu", short="Vốn chủ", desc="Vốn chủ âm nghĩa là nợ lớn hơn tài sản.", tiers="vốn chủ âm: +3 điểm (tự động mức Thận trọng)"),
]
BANDS = [dict(k="good", label="Tốt", pts="0 điểm", desc="Không chỉ số nào chạm ngưỡng cảnh báo."), dict(k="watch", label="Theo dõi", pts="1–2 điểm", desc="Có 1–2 chỉ số chạm ngưỡng: nên hỏi thêm khi cấp công nợ/ tạm ứng."),
         dict(k="caution", label="Thận trọng", pts="từ 3 điểm", desc="Nhiều chỉ số xấu cùng lúc: cân nhắc bảo lãnh, giới hạn tạm ứng, thanh toán theo tiến độ chặt.")]
def vn(x, d=1): return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def score(periods):
    """periods: danh sách đã tính metrics, mới nhất đầu tiên. Trả về nhãn + từng chỉ số (kể cả chỉ số không kích hoạt) để hiển thị minh bạch."""
    p0 = periods[0]; v = p0["v"]; m = p0["m"]; p1 = periods[1] if len(periods) > 1 else None
    need = ("rev", "np", "liab", "eq", "ca", "cl", "cfo", "ar")
    if any(v.get(k) is None for k in need): return dict(k="nodata", label="Chưa đủ dữ liệu", pts=None, items=[], basis=p0["id"])
    items = []; add = lambda id, val, pts, say: items.append(dict(id=id, val=val, pts=pts, status="bad" if pts >= 2 else "warn" if pts == 1 else "ok", say=say))
    if v["eq"] <= 0: add("eq", "âm", 3, f"Vốn chủ sở hữu âm ({vn(v['eq']/1e9,0)} tỷ): nợ lớn hơn tài sản.")
    else: add("eq", f"{vn(v['eq']/1e9,0)} tỷ", 0, f"Vốn chủ sở hữu dương ({vn(v['eq']/1e9,0)} tỷ đồng).")
    x = m["dbe"]
    if x is not None:
        pts = 2 if x > 2 else 1 if x > 1 else 0
        add("lev", f"{vn(x,2)} lần", pts, f"Nợ vay bằng {vn(x,2)} lần vốn chủ" + (" – rất cao so với ngưỡng 2,0 lần." if pts == 2 else " – cao hơn ngưỡng 1,0 lần." if pts == 1 else " – trong ngưỡng an toàn (≤ 1,0 lần)."))
    x = m["cr"]; pts = 2 if x < 1 else 1 if x < 1.2 else 0
    add("cr", vn(x, 2), pts, f"Thanh khoản hiện hành {vn(x,2)}" + (" – dưới 1,0: tài sản ngắn hạn không đủ trả nợ ngắn hạn." if pts == 2 else " – hơi thấp so với ngưỡng 1,2." if pts == 1 else " – đủ trả nợ ngắn hạn (≥ 1,2)."))
    neg0 = v["cfo"] < 0; neg1 = bool(p1 and p1["v"]["cfo"] < 0 and p1["months"] == p0["months"])
    pts = (2 if neg1 else 1) if neg0 else 0
    add("cfo", f"{vn(v['cfo']/1e9,0)} tỷ", pts, ("Dòng tiền kinh doanh âm " + vn(v["cfo"] / 1e9, 0) + " tỷ" + (" và cũng âm ở kỳ liền trước – kéo dài nhiều kỳ." if neg1 else " (kỳ liền trước dương hoặc không có số).")) if neg0 else f"Dòng tiền kinh doanh dương ({vn(v['cfo']/1e9,0)} tỷ) – lợi nhuận có tiền thật đi kèm.")
    x = m["nm"]; pts = 2 if x <= 0 else 1 if x < 0.01 else 0
    add("nm", f"{vn(x*100,1)}%", pts, f"Biên lợi nhuận ròng {vn(x*100,1)}%" + (" – đang lỗ." if pts == 2 else " – rất mỏng (< 1%)." if pts == 1 else " – không chạm ngưỡng cảnh báo."))
    x = m["dso"]; pts = 2 if x > 240 else 1 if x > 150 else 0
    add("dso", f"{vn(x,0)} ngày", pts, f"Phải thu khách hàng tương đương {vn(x,0)} ngày doanh thu" + (f" – rất dài so với ngưỡng 240 ngày." if pts == 2 else f" – hơi dài so với ngưỡng 150 ngày." if pts == 1 else " – trong ngưỡng 150 ngày."))
    if p1 and p1["months"] == p0["months"]:
        g = v["rev"] / p1["v"]["rev"] - 1; pts = 1 if g < -0.2 else 0
        add("gr", f"{'+' if g>=0 else '−'}{vn(abs(g)*100,1)}%", pts, f"Doanh thu {'giảm' if g<0 else 'tăng'} {vn(abs(g)*100,1)}% so với {p1['label'].split(' (')[0].lower()}" + (" – giảm mạnh (> 20%)." if pts else "."))
    else: items.append(dict(id="gr", val="–", pts=0, status="na", say="Chưa có kỳ liền trước cùng độ dài để so doanh thu."))
    pts = sum(i["pts"] for i in items); k = "good" if pts == 0 else "watch" if pts <= 2 else "caution"
    return dict(k=k, label={"good": "Tốt", "watch": "Theo dõi", "caution": "Thận trọng"}[k], pts=pts, items=items, basis=p0["id"])
def fin_flags(periods, label):
    """Cờ rủi ro rút từ số liệu thật (không phải tin tức)."""
    p0 = periods[0]; v = p0["v"]; m = p0["m"]; fl = []
    if v["cfo"] < 0: fl.append(dict(sev="warn", t="Dòng tiền kinh doanh âm", d=f"CFO {p0['label'].split(' (')[0].lower()}: {vn(v['cfo']/1e9,0)} tỷ đồng."))
    if m["cr"] < 1: fl.append(dict(sev="warn", t="Thanh khoản hiện hành dưới 1", d=f"TSNH ÷ nợ ngắn hạn = {vn(m['cr'],2)}."))
    if v["cfo"] >= 0 and len(periods) > 1 and periods[1]["v"]["cfo"] < 0 and periods[1]["months"] == p0["months"]:
        fl.append(dict(sev="info", t="Dòng tiền kinh doanh kỳ liền trước âm", d=f"{periods[1]['id']}: {vn(periods[1]['v']['cfo']/1e9,0)} tỷ đồng; kỳ mới nhất đã dương lại."))
    if v["np"] < 0: fl.append(dict(sev="bad", t="Đang lỗ", d=f"LNST {vn(v['np']/1e9,0)} tỷ đồng."))
    if len(periods) > 1 and periods[1]["months"] == p0["months"]:
        g = v["rev"] / periods[1]["v"]["rev"] - 1
        if g < -0.2: fl.append(dict(sev="warn", t="Doanh thu giảm mạnh", d=f"Giảm {vn(abs(g)*100,1)}% so với kỳ liền trước."))
        if v["np"] > 0 and periods[1]["v"]["np"] > 0 and v["np"] / periods[1]["v"]["np"] - 1 < -0.5: fl.append(dict(sev="warn", t="Lợi nhuận giảm hơn một nửa", d=f"LNST giảm {vn(abs(v['np']/periods[1]['v']['np']-1)*100,0)}% so với kỳ liền trước."))
    if m["fin_share"] is not None and m["fin_share"] > 0.6 and v["fin_inc"] > 0.25 * v["np"]:
        fl.append(dict(sev="info", t="Lợi nhuận phụ thuộc thu nhập tài chính", d=f"Doanh thu hoạt động tài chính {vn(v['fin_inc']/1e9,0)} tỷ ≈ {vn(m['fin_share']*100,0)}% lợi nhuận trước thuế ({vn(v['pbt']/1e9,0)} tỷ) – không đến từ hoạt động xây lắp/kinh doanh chính."))
    return fl
def build_fin(tk, c):
    ps = []
    for p in sorted(c["periods"], key=lambda x: x["end"], reverse=True):
        checks = check_period(tk, p); ps.append(dict(id=p["id"], label=p["label"], start=p["start"], end=p["end"], months=p["months"], audit=p["audit"], source=p["source"], v=p["v"], m=metrics(p), notes=p.get("notes", []), xref=p.get("xref"), checks=checks))
    lab = score(ps); fl = fin_flags(ps, lab)
    out = dict(ticker=c["ticker"], exchange=c["exchange"], basis=c["basis"], fy_note=c["fy_note"], auditor=c["auditor"], note=c.get("note"), ir_url=c.get("ir_url"), newer=c.get("newer"), periods=ps, label=lab, flags=fl,
               verified_on=None)
    return out

# ---------- 3) build ----------
def build():
    units = J(UNITS_F)["units"]; fin = J(FIN_F); reg = J(REG_F, {"records": {}})["records"]; orgs = {o["name"]: o for o in J(os.path.join(DATA, "orgs.json"))["orgs"]}
    out_units = []
    for u in units:
        o = orgs[u["org"]]; r = reg.get(u["mst"]); fl = []
        if not r: raise SystemExit(f"Thiếu bản ghi đăng ký cho MST {u['mst']} ({u['org']}) – chạy --refresh-registry")
        status_ok = (r["status"] or "").strip().lower() == "nnt đang hoạt động"
        if not status_ok: fl.append(dict(sev="bad" if "không hoạt động" in r["status"].lower() or "ngừng" in r["status"].lower() or "chấm dứt" in r["status"].lower() else "warn", t="Tình trạng thuế khác 'đang hoạt động'", d=f"Cơ quan thuế ghi: “{r['status']}”. Cần hỏi lại đơn vị trước khi ký/ứng tiền."))
        hub_legal = o.get("legal")
        if hub_legal and norm_name(hub_legal) != norm_name(r["legal"]):
            fl.append(dict(sev="warn", t="Tên pháp nhân cần xác nhận", d=f"Danh sách theo dõi của hub ghi “{hub_legal}”, bản ghi thuế ghi “{r['legal']}”. Bảng này hiển thị tên theo bản ghi thuế – hãy đối chiếu với hợp đồng/giấy phép đăng ký của đơn vị."))
        if not hub_legal and u.get("name_unconfirmed"):
            fl.append(dict(sev="warn", t="Tên pháp nhân cần xác nhận", d="Hub chưa ghi tên pháp nhân của đơn vị này; MST được chọn theo tên thương hiệu và khớp bản ghi thuế, nhưng chưa có xác nhận từ hợp đồng/website. Hãy đối chiếu trước khi dùng."))
        f = None
        if u.get("fin"):
            f = build_fin(u["fin"], fin["companies"][u["fin"]]); f["verified_on"] = fin["verified_on"]
        al = {strip(a) for a in u.get("aliases", [])} | {strip(o["name"])}
        for k in ("short",): al.add(strip(o.get(k) or ""))
        al |= {strip(b) for b in o.get("brands", [])}; al |= {strip(r["legal"]), strip(r.get("intl") or ""), strip(r.get("short") or "")}
        if f: al.add(strip(f["ticker"]))
        out_units.append(dict(id=re.sub(r"[^a-z0-9]+", "-", strip(u["org"])).strip("-"), org=u["org"], name=r["legal"], short=u["org"], group=o.get("group"), website=o.get("website") if (o.get("website") or "").startswith("http") else None,
            mst=u["mst"], aliases=sorted(a for a in al if a), listed=bool(f), ticker=f["ticker"] if f else None, exchange=f["exchange"] if f else None, note=u.get("note"),
            hub_note=o.get("note"), reg=dict(legal=r["legal"], intl=r.get("intl"), address=r["address"], status=r["status"], active=status_ok, fetched=r["fetched"], upstream_updated=r.get("upstream_updated"),
                source="VietQR API (dữ liệu tổng hợp từ Tổng cục Thuế)", url="https://api.vietqr.io/v2/business/" + u["mst"]), flags=fl, fin=f))
    doc = dict(schema=1, generated=TODAY.isoformat(), stale_days=STALE_DAYS, old_period_days=OLD_PERIOD_DAYS, rules=RULES, bands=BANDS, units=out_units,
        links=[dict(k="mst", t="Tra cứu mã số thuế / tình trạng người nộp thuế (Tổng cục Thuế)", u="https://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp", why="đối chiếu tên, địa chỉ, tình trạng với bản ghi gốc"),
               dict(k="dkkd", t="Cổng thông tin quốc gia về đăng ký doanh nghiệp", u="https://dangkykinhdoanh.gov.vn", why="xem vốn điều lệ, người đại diện, ngành nghề, công bố thông tin doanh nghiệp"),
               dict(k="msc", t="Hệ thống mạng đấu thầu quốc gia (muasamcong)", u="https://muasamcong.mof.gov.vn", why="tìm thông tin nhà thầu, kết quả thầu và mục nhà thầu bị xử lý vi phạm (tên mục có thể thay đổi)"),
               dict(k="inv", t="Tổng cục Thuế – công khai thông tin doanh nghiệp rủi ro/ nợ thuế", u="https://www.gdt.gov.vn", why="tra danh sách doanh nghiệp rủi ro về hóa đơn, nợ thuế do cơ quan thuế công bố")],
        disclaimer="Nhãn chỉ là công cụ hỗ trợ sàng lọc nhanh dựa trên số liệu BCTC đã kiểm toán, không phải xếp hạng tín nhiệm hay kết luận về doanh nghiệp. Ngưỡng điểm là ước định cho ngành xây dựng và có thể điều chỉnh.")
    os.makedirs(DATA, exist_ok=True); json.dump(doc, open(OUT_F, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"suppliers.json: {len(out_units)} đơn vị, {sum(1 for u in out_units if u['fin'])} có BCTC kiểm chứng -> {os.path.relpath(OUT_F)}")
    for u in out_units:
        if u["fin"]: print(f"  {u['ticker']:4} {u['fin']['periods'][0]['id']:7} {u['fin']['label']['label']:12} điểm={u['fin']['label']['pts']}")
def check_age():
    d = J(OUT_F); bad = 0
    if not d: print("Chưa có suppliers.json"); return 1
    for u in d["units"]:
        for lab, dstr in (("đăng ký/tình trạng thuế", u["reg"]["fetched"]), ("BCTC (ngày kiểm chứng)", u["fin"]["verified_on"] if u["fin"] else None)):
            if dstr and (TODAY - dt.date.fromisoformat(dstr)).days > STALE_DAYS: print(f"CẢNH BÁO {u['org']}: {lab} lấy ngày {dstr} (> {STALE_DAYS} ngày) – cần cập nhật tay"); bad += 1
        if u["fin"]:
            e = u["fin"]["periods"][0]["end"]; age = (TODAY - dt.date.fromisoformat(e)).days
            if age > OLD_PERIOD_DAYS or u["fin"].get("newer"): print(f"LƯU Ý {u['org']}: kỳ mới nhất kết thúc {e} ({age} ngày)" + (f"; đã có BCTC mới hơn: {u['fin']['newer']['label']}" if u["fin"].get("newer") else ""))
    print("OK – không có dữ liệu quá hạn" if not bad else f"{bad} cảnh báo"); return 0
if __name__ == "__main__":
    if "--refresh-registry" in sys.argv: refresh_registry()
    elif "--check" in sys.argv: sys.exit(check_age())
    else: build()
