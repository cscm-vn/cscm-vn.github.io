#!/usr/bin/env python3
"""Dữ liệu cho AI/LLM: sinh ở GỐC site, mỗi lần CI build (gọi cuối trends/build.py::main, sau khi site/data/*.json đã đủ):
  prices.csv (giá mới nhất, phẳng) · hub.sqlite (bảng meta/items/prices_latest/price_history/suppliers/supplier_fin/news/compare_hn_hcm/…)
  llms.txt (hướng dẫn cho AI) · robots.txt · sitemap.xml.
Chỉ dùng file ĐÃ công khai trên site (prices.json, history/*.json, data/*.json); không thêm số ước tính, không gọi mạng."""
import os, re, csv, json, glob, time, sqlite3, subprocess, unicodedata, datetime as dt
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); SITE = os.path.join(ROOT, "site"); D = os.path.join(SITE, "data")
TZ = dt.timezone(dt.timedelta(hours=7)); BASE = "https://cscm-vn.github.io/"
def J(p, default=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return default
def strip(s):
    s = unicodedata.normalize("NFD", (s or "").lower()); return "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
def nfc(s): return unicodedata.normalize("NFC", s) if isinstance(s, str) else s
def commit():
    sha = os.environ.get("GITHUB_SHA")
    if sha: return sha[:7]
    try: return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
    except Exception: return "unknown"
def vat_status(note):
    n = strip(note)
    if "khong ghi ro vat" in n: return "không rõ"
    if "da gom vat" in n or "da bao gom vat" in n: return "đã gồm VAT"
    if "chua vat" in n or "chua gom vat" in n or "chua bao gom vat" in n: return "chưa VAT"
    return "không nêu"
def slump_of(name):
    m = re.search(r"sụt\s*(\d+\s*±\s*\d+)", name or "")
    return m.group(1).replace(" ", "") if m else None
def num(v): return None if v is None else v

SCHEMA = """
create table meta(key text primary key, value text);
create table taxonomy(id text primary key, parent_id text, level integer, name text);
create table items(id text primary key, name text, category text, scope text, region_label text, reg text, tax_id text, tax_name text, tax_group text,
  master_code text, master_name text, master_conf text, unit text, currency text, source text, source_url text, conditions text, vat_status text, slump text,
  slump12_add real, first_date text, n_hist integer, mat_hang_url text);
create table prices_latest(item_id text primary key references items(id), as_of text, price real, price_high real, unit text, currency text, vnd real, vnd_unit text,
  prev_price real, d1_pct real, w1_pct real, mom_pct real, yoy_pct real, s0_pct real, first_date text, n_hist integer, is_new integer, stale integer, last_ok text);
create table price_history(item_id text references items(id), date text, price real, price_high real, primary key(item_id, date));
create table compare_hn_hcm(label text primary key, tax_id text, unit text, hn real, hcm real, diff_pct real, basis text, hn_ids text, hcm_ids text, insight text);
create table compare_parts(label text, region text, item_id text, source text, raw real, norm real);
create table suppliers(id text primary key, org text, name text, short text, grp text, website text, tax_code text, listed integer, ticker text, exchange text,
  legal_name text, address text, tax_status text, tax_active integer, reg_fetched text, reg_source_url text, has_fin integer, fin_label text, fin_label_pts integer,
  name_needs_confirm integer, flags text, flag_details text, note text, hub_note text);
create table supplier_fin(supplier_id text references suppliers(id), period_id text, label text, start_date text, end_date text, months integer, audit text, basis text,
  source_title text, source_url text, rev integer, cogs integer, gp integer, fin_inc integer, pbt integer, np integer, ta integer, ca integer, cl integer, liab integer,
  eq integer, ar integer, inv integer, cash integer, sti integer, debt_st integer, debt_lt integer, cfo integer, primary key(supplier_id, period_id));
create table news(id text, kind text, date text, title text, segment text, region text, summary text, takeaway text, tax_id text, source_name text, source_url text, all_source_urls text, extra text);
create index news_k on news(kind, date); create index ph_d on price_history(date);
"""
COLDOC = {
 "meta": {"key": "tên", "value": "giá trị (văn bản)"},
 "taxonomy": {"id": "mã nhóm trên hub (vd xd.be-tong); cấp 1 = xd, mep, ht, md, elv, cq, esg, tt", "parent_id": "mã nhóm cha (rỗng = cấp 1)", "level": "1 hoặc 2", "name": "tên nhóm"},
 "items": {"id": "mã mặt hàng (khóa; = hub.json items[].id = tên file history/<id>.json)", "name": "tên mặt hàng (thường kèm nguồn trong ngoặc)", "category": "danh mục của nguồn", "scope": "vn | world",
  "region_label": "vùng ghi trên nguồn (Hà Nội, TP.HCM, Miền Bắc, Miền Nam, Miền Trung…; rỗng với hàng thế giới)", "reg": "vùng chuẩn hoá: hn | hcm | vn (VN khác) | world", "tax_id": "nhóm cấp 2 của hub (taxonomy.id)",
  "tax_name": "tên nhóm cấp 2", "tax_group": "tên nhóm cấp 1", "master_code": "mã nhóm giá master data (có thể rỗng)", "master_name": "tên nhóm giá master data", "master_conf": "độ tin cậy gán nhóm (high | medium | low | none, như hub.json mt_conf)",
  "unit": "đơn vị giá", "currency": "VND | USD | CNY", "source": "tên nguồn", "source_url": "link nguồn", "conditions": "ghi chú điều kiện giá NGUYÊN VĂN từ nguồn (VAT, vận chuyển, bơm, sụt…)",
  "vat_status": "suy từ conditions: 'chưa VAT' | 'đã gồm VAT' | 'không rõ' | 'không nêu' (conditions không nhắc VAT)", "slump": "độ sụt ghi trong tên (vd 12±2, 10±2) hoặc rỗng", "slump12_add": "phụ phí tăng sụt 10±2→12±2 do chính NCC công bố (VND/m³), có thể rỗng",
  "first_date": "ngày đầu tiên hub thu được giá mã này", "n_hist": "số điểm lịch sử (số ngày có giá)", "mat_hang_url": "trang chi tiết mã trên hub"},
 "prices_latest": {"item_id": "→ items.id", "as_of": "ngày giá của nguồn (YYYY-MM-DD)", "price": "giá (theo unit; nếu có khoảng thì là cận thấp)", "price_high": "cận cao của khoảng giá (rỗng nếu giá đơn)", "unit": "đơn vị", "currency": "tiền tệ",
  "vnd": "quy đổi VND (chỉ hàng thế giới; tỷ giá Vietcombank chuyển khoản, chưa thuế/phí/vận chuyển)", "vnd_unit": "đơn vị của vnd", "prev_price": "giá lần quan sát trước", "d1_pct": "% so với lần quan sát trước (hoặc % do nguồn cung cấp)",
  "w1_pct": "% so với điểm lịch sử cách ~7 ngày", "mom_pct": "% so với ~30 ngày", "yoy_pct": "% so với ~365 ngày", "s0_pct": "% từ ngày đầu thu (first_date) đến giá mới nhất; rỗng nếu <2 điểm",
  "first_date": "ngày đầu thu", "n_hist": "số điểm lịch sử", "is_new": "1 = 'mới thu' (chỉ <2 điểm, chưa có % thay đổi)", "stale": "1 = dữ liệu cũ (nguồn lỗi hoặc >30 giờ chưa cập nhật)", "last_ok": "thời điểm lấy thành công gần nhất (ISO, +07:00)"},
 "price_history": {"item_id": "→ items.id", "date": "ngày giá", "price": "giá", "price_high": "cận cao (nếu có)"},
 "compare_hn_hcm": {"label": "tên cặp so sánh", "tax_id": "nhóm", "unit": "đơn vị", "hn": "giá Hà Nội (đã làm tròn)", "hcm": "giá TP.HCM (đã làm tròn)", "diff_pct": "(hcm/hn − 1)×100; dương = TP.HCM cao hơn",
  "basis": "rmc = bê tông quy về cơ sở chung (xem llms.txt) | steel = thép giá niêm yết nhà máy theo miền | sxd = khác cơ sở (HN: công bố Sở XD; HCM: bình quân/tại mỏ) – chỉ tham khảo xu hướng", "hn_ids": "các items.id dùng cho Hà Nội (phân tách bằng dấu phẩy)", "hcm_ids": "các items.id dùng cho TP.HCM", "insight": "diễn giải của hub (có nêu cơ sở so sánh)"},
 "compare_parts": {"label": "→ compare_hn_hcm.label (chỉ basis=rmc)", "region": "hn | hcm", "item_id": "→ items.id", "source": "nguồn/NCC", "raw": "giá niêm yết (trung điểm nếu có khoảng)", "norm": "giá sau quy đổi cơ sở chung (chưa VAT, sụt 12±2, chưa bơm); trung vị các norm của một vùng = cột hn/hcm của compare_hn_hcm"},
 "suppliers": {"id": "mã đơn vị", "org": "tên theo dõi", "name": "tên trong danh sách theo dõi của hub", "short": "tên ngắn", "grp": "nhóm ngành", "website": "website", "tax_code": "mã số thuế đã hiển thị công khai trên hub", "listed": "1 = niêm yết", "ticker": "mã CK", "exchange": "sàn",
  "legal_name": "tên pháp nhân theo bản ghi thuế (VietQR/Tổng cục Thuế) hub đã lấy", "address": "địa chỉ theo bản ghi thuế", "tax_status": "tình trạng NNT", "tax_active": "1 = đang hoạt động", "reg_fetched": "ngày hub lấy bản ghi thuế", "reg_source_url": "nguồn bản ghi thuế",
  "has_fin": "1 = hub có BCTC công khai đã kiểm toán trong supplier_fin; 0 = 'Chưa có BCTC công khai' (KHÔNG có số, đừng suy đoán)", "fin_label": "nhãn sàng lọc của hub khi có BCTC (Tốt/Theo dõi/…; không phải xếp hạng tín nhiệm)", "fin_label_pts": "điểm của nhãn",
  "name_needs_confirm": "1 = đơn vị có cờ 'Tên pháp nhân cần xác nhận' trong suppliers.json (lý do nằm ở flag_details: hoặc tên trong danh sách theo dõi của hub khác bản ghi thuế, hoặc hub chưa ghi tên pháp nhân và MST chọn theo tên thương hiệu; cần đối chiếu hợp đồng/giấy phép/website trước khi dùng tên)", "flags": "tiêu đề các cờ cảnh báo, phân tách ' | '", "flag_details": "nội dung các cờ", "note": "ghi chú", "hub_note": "ghi chú của hub"},
 "supplier_fin": {"supplier_id": "→ suppliers.id", "period_id": "kỳ (vd FY2026)", "label": "mô tả kỳ", "start_date": "bắt đầu kỳ", "end_date": "kết thúc kỳ", "months": "số tháng", "audit": "mức soát xét/kiểm toán", "basis": "hợp nhất/riêng lẻ", "source_title": "tên tài liệu BCTC", "source_url": "link BCTC",
  "rev": "doanh thu thuần (VND)", "cogs": "giá vốn", "gp": "lợi nhuận gộp", "fin_inc": "doanh thu tài chính", "pbt": "lợi nhuận trước thuế", "np": "lợi nhuận sau thuế", "ta": "tổng tài sản", "ca": "tài sản ngắn hạn", "cl": "nợ ngắn hạn", "liab": "nợ phải trả", "eq": "vốn chủ sở hữu",
  "ar": "phải thu", "inv": "hàng tồn kho", "cash": "tiền", "sti": "đầu tư tài chính ngắn hạn", "debt_st": "vay ngắn hạn", "debt_lt": "vay dài hạn", "cfo": "dòng tiền hoạt động kinh doanh (tất cả đơn vị VND, số nguyên, đúng như BCTC hub đã nhập)"},
 "news": {"id": "mã tin", "kind": "market (tin thị trường) | legal (văn bản pháp luật) | scm (tín hiệu cung–cầu theo nhóm hàng) | trend (xu hướng)", "date": "ngày tin (scm: ngày cập nhật)", "title": "tiêu đề", "segment": "market: phân khúc/chủ đề (Nhân công, Chính sách…); legal: loại văn bản; scm: nhãn tín hiệu; trend: danh mục",
  "region": "vùng", "summary": "tóm tắt", "takeaway": "market: 'hàm ý' mua sắm/đấu thầu; legal: tác động; scm: thời điểm/khuyến nghị; trend: ý nghĩa", "tax_id": "nhóm hub (có thể nhiều, phân tách dấu phẩy)", "source_name": "nguồn đầu tiên", "source_url": "link nguồn đầu tiên", "all_source_urls": "mọi link nguồn", "extra": "legal: số hiệu/hiệu lực; trend: điểm; scm: xu hướng giá"},
}
SQL_EX = [
 ("Giá bê tông M400 ở TP.HCM hôm nay và điều kiện của từng nhà cung cấp", "select i.name, p.price, p.price_high, p.unit, p.as_of, i.vat_status, i.slump, i.slump12_add, i.conditions from items i join prices_latest p on p.item_id=i.id where i.name like 'Bê tông tươi M400%' and i.reg='hcm' order by i.name;"),
 ("So sánh Hà Nội – TP.HCM bê tông M400 (đã quy về cơ sở chung) và các thành phần", "select c.label, c.unit, c.hn, c.hcm, c.diff_pct, c.basis from compare_hn_hcm c where c.label like '%M400%'; -- thành phần: select * from compare_parts where label like '%M400%';"),
 ("10 mã tăng nhiều nhất từ một ngày cố định (đổi '2026-10-22'; so điểm đầu tiên từ ngày đó với giá mới nhất)", "select i.id, i.name, h0.date as d0, h0.price as p0, p.price as p1, round((p.price/h0.price-1)*100,2) as pct from prices_latest p join items i on i.id=p.item_id join price_history h0 on h0.item_id=p.item_id and h0.date=(select min(date) from price_history where item_id=p.item_id and date>='2026-10-22') where h0.date<p.as_of and h0.price>0 order by pct desc limit 10;"),
 ("10 mã tăng nhiều nhất tính từ NGÀY ĐẦU THU của chính mã đó (s0_pct; độ dài lịch sử khác nhau, chỉ mã có ≥2 điểm)", "select p.item_id, i.name, p.first_date, round(p.s0_pct,2) as s0_pct, p.price, p.unit from prices_latest p join items i on i.id=p.item_id where p.n_hist>=2 and p.s0_pct is not null order by p.s0_pct desc limit 10;"),
 ("Lịch sử giá một mã (đổi item_id)", "select date, price, price_high from price_history where item_id='rmc_hcm_mk_m400' order by date;"),
 ("Nhà cung cấp nào có BCTC công khai và doanh thu kỳ mới nhất", "select s.short, s.ticker, f.period_id, f.end_date, f.rev, f.np, f.source_url from suppliers s join supplier_fin f on f.supplier_id=s.id where f.end_date=(select max(end_date) from supplier_fin where supplier_id=s.id) order by f.rev desc;"),
 ("Một nhà cung cấp cụ thể có BCTC không? (has_fin=0 nghĩa là KHÔNG có số)", "select short, org, tax_code, has_fin, fin_label, name_needs_confirm from suppliers where short like '%Newtecons%' or org like '%Newtecons%';"),
 ("Đơn vị bị cờ 'Tên pháp nhân cần xác nhận'", "select short, name, legal_name, flag_details from suppliers where name_needs_confirm=1 order by short;"),
 ("Tin thị trường chủ đề Nhân công và hàm ý mua sắm/đấu thầu", "select date, title, takeaway, source_url from news where kind='market' and segment='Nhân công' order by date desc limit 10;"),
]
FILES_DOC = [  # (đường dẫn, mô tả) – chỉ liệt kê nếu file có thật
 ("llms.txt", "Hướng dẫn này."),
 ("prices.csv", "Giá MỚI NHẤT mọi mặt hàng (1 dòng/mã), phẳng, UTF-8 không BOM, cột generated_at ở đầu. Mô tả cột ở mục 4."),
 ("hub.sqlite", "SQLite: toàn bộ dữ liệu trên dạng bảng (meta, items, prices_latest, price_history, compare_hn_hcm, compare_parts, suppliers, supplier_fin, news, taxonomy). Cách đọc ở mục 7."),
 ("data/hub.json", "Nguồn chuẩn của giá cho các trang hub: items[] (mỗi mã: giá, thay đổi %, nhóm, vùng, sparkline, tháng), compare[] (Hà Nội vs TP.HCM), steel_brand_pairs[], digest[] (tổng hợp tháng), mom_movers[] (id 12 mã đổi nhiều nhất theo tháng)."),
 ("data/trk.json", "Chuỗi giá rút gọn để vẽ cột 'Xu hướng': {id:{s: ngày đầu, o:[số ngày cách s], p:[giá]}}, 60 điểm cuối, chỉ mã có ≥2 điểm."),
 ("history/<mã>.json", "Lịch sử đầy đủ của 1 mã: {id, points:[{date, price, price_high?}]}. 1 file/mã (id lấy từ items[].id). Gộp sẵn: lich-su-gia.csv và bảng price_history. Ví dụ: {EX}"),
 ("prices.json", "Bảng giá thô từ app (items[] có currency, prev, change_pct, status, stale, last_ok; sources[] = nhật ký chạy từng nguồn; updated_at; usd_vnd)."),
 ("bang-gia.csv · bang-gia.xlsx", "Bảng giá mới nhất cho người dùng Excel (tiêu đề tiếng Việt, CSV có BOM, kèm nhóm master data). prices.csv là bản gọn cho máy đọc."),
 ("lich-su-gia.csv", "LỊCH SỬ giá mọi mã gộp 1 file (Ngày giá, Mã, Mặt hàng, Danh mục, Khu vực, Giá, Giá cao, Đơn vị, Tiền tệ, Nguồn) – có BOM. Thay cho 'prices-history.csv' (không tạo file trùng); cùng dữ liệu với bảng price_history."),
 ("data/market.json", "Tin thị trường biên tập (segment, region, date, summary, takeaway = hàm ý mua sắm/đấu thầu, tax, sources[])."),
 ("data/trends.json", "Xu hướng vật liệu/thiết kế/công nghệ (score 0–100, why, impact, sources[])."),
 ("data/feed.json · data/legal-feed.json · data/policy-feed.json", "Tin tự động (RSS/Google News) theo từ khóa – CHƯA biên tập, có thể nhiễu."),
 ("data/suppliers.json", "Nhà cung cấp/nhà thầu: units[] (bản ghi thuế reg, flags, fin = BCTC kiểm toán nếu có), rules/bands/disclaimer của nhãn sàng lọc."),
 ("data/legal.json", "Văn bản pháp luật mới (kind, issuer, number, issued, effective, status, summary, impact, sources[])."),
 ("data/scm.json", "Tín hiệu cung–cầu theo 14 nhóm hàng (signal, trend, headline, supply/demand/trade, rec, timing, sources[]), cước vận tải, giả định."),
 ("data/landed-cost.json", "Máy tính landed cost hàng Trung Quốc vs nội địa (FOB, thuế… là GIẢ ĐỊNH minh hoạ – đọc assumptions/gaps trước khi dùng)."),
 ("data/dieu-chinh.json · dieu-chinh.csv", "Theo dõi giá thị trường so với đơn giá nguyên tắc HĐ tổng thầu (CTD/NTC)."),
 ("forecast.json", "Dự báo 3/6/12 tháng (base/lo/hi, bull/bear) – ước lượng thống kê, không cam kết."),
 ("data/segments.json", "Phân tích phân khúc BĐS Hà Nội vs TP.HCM (có dòng 'ƯỚC TÍNH' do nguồn – đọc nhãn)."),
 ("data/taxonomy.json · data/mt.json", "Cây nhóm của hub; cây nhóm giá master data + ánh xạ mã."),
 ("data/highlights.json · data/orgs.json · data/quiz.json · data/checklist.json", "Dữ liệu phục vụ giao diện (điểm nhấn trang chủ, danh sách đơn vị theo dõi, câu hỏi ôn, checklist)."),
 ("sitemap.xml · robots.txt", "Danh sách trang và quyền đọc."),
]
def build_taxonomy():
    t = J(os.path.join(D, "taxonomy.json"), {"tree": []}); rows = []
    for n in t["tree"]:
        rows.append((n["id"], None, 1, n["name"]))
        for c in n.get("children", []): rows.append((c["id"], n["id"], 2, c["name"]))
    return rows
def main(site=None):
    t0 = time.time(); global SITE, D
    if site: SITE = site; D = os.path.join(SITE, "data")
    now = dt.datetime.now(TZ).isoformat(timespec="minutes"); sha = commit()
    hub = J(os.path.join(D, "hub.json")); prices = J(os.path.join(SITE, "prices.json"), {"items": []})
    if not hub: print("aidata: thiếu hub.json – bỏ qua"); return
    pj = {x["id"]: x for x in prices["items"]}; tax = build_taxonomy(); taxn = {r[0]: r for r in tax}
    mt = J(os.path.join(D, "mt.json"), {"nodes": []}); mtn = {n["code"]: n["name_vi"] for n in mt.get("nodes", [])}
    # ---- prices.csv + bảng items/prices_latest/price_history
    items_rows, pl_rows, hist_rows, csv_rows = [], [], [], []
    for x in hub["items"]:
        p = pj.get(x["id"], {}); t2 = taxn.get(x["tax"]); t1 = taxn.get(t2[1]) if t2 else None
        url = f"{BASE}mat-hang.html?id={x['id']}"; cur = p.get("currency"); vs = vat_status(x.get("note")); sl = slump_of(x["name"]); nh = x.get("n_hist") or 0; new = 1 if nh < 2 else 0
        items_rows.append((x["id"], x["name"], x.get("category"), x.get("grp"), x.get("region"), x.get("reg"), x.get("tax"), t2[3] if t2 else None, t1[3] if t1 else None,
                           x.get("mt"), mtn.get(x.get("mt")), x.get("mt_conf"), x.get("unit"), cur, x.get("src"), x.get("url"), x.get("note"), vs, sl, x.get("slump12_add"), x.get("first_date"), nh, url))
        pl_rows.append((x["id"], x.get("as_of"), x.get("price"), x.get("price_high"), x.get("unit"), cur, x.get("vnd"), x.get("vnd_unit"), p.get("prev"), x.get("d1"), x.get("w1"), x.get("mom"), x.get("yoy"), x.get("s0"),
                        x.get("first_date"), nh, new, 1 if x.get("stale") else 0, p.get("last_ok")))
        h = J(os.path.join(SITE, "history", x["id"] + ".json"), {"points": []})
        for pt in sorted(h.get("points", []), key=lambda q: q["date"]):
            if pt.get("price") is not None: hist_rows.append((x["id"], pt["date"], pt["price"], pt.get("price_high")))
        csv_rows.append([now, x["id"], x["name"], t1[3] if t1 else "", t2[3] if t2 else "", mtn.get(x.get("mt")) or "", x.get("category") or "", x.get("region") or "", x.get("reg") or "", x.get("src") or "", x.get("as_of") or "",
                         x.get("price"), x.get("price_high"), x.get("unit") or "", cur or "", x.get("vnd"), x.get("vnd_unit") or "", x.get("note") or "", vs, sl or "", x.get("slump12_add"),
                         x.get("d1"), x.get("w1"), x.get("mom"), x.get("yoy"), x.get("s0"), x.get("first_date") or "", nh, new, 1 if x.get("stale") else 0, x.get("url") or "", url])
    CSV_HDR = ["generated_at", "item_id", "name", "group_site", "group_subsite", "group_master", "category", "region_label", "reg", "source", "as_of", "price", "price_high", "unit", "currency", "vnd", "vnd_unit",
               "conditions", "vat_status", "slump", "slump12_add", "d1_pct", "w1_pct", "mom_pct", "yoy_pct", "s0_pct", "first_date", "n_hist", "is_new", "stale", "source_url", "mat_hang_url"]
    with open(os.path.join(SITE, "prices.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(CSV_HDR)
        for r in csv_rows: w.writerow([nfc(v) if isinstance(v, str) else ("" if v is None else v) for v in r])
    # ---- hub.sqlite
    dbp = os.path.join(SITE, "hub.sqlite"); tmp = dbp + ".tmp"
    if os.path.exists(tmp): os.remove(tmp)
    db = sqlite3.connect(tmp); db.executescript(SCHEMA)
    db.executemany("insert into taxonomy values (?,?,?,?)", tax)
    db.executemany("insert into items values (" + ",".join("?" * 23) + ")", items_rows)
    db.executemany("insert into prices_latest values (" + ",".join("?" * 19) + ")", pl_rows)
    db.executemany("insert into price_history values (?,?,?,?)", hist_rows)
    for c in hub.get("compare", []):
        db.execute("insert into compare_hn_hcm values (?,?,?,?,?,?,?,?,?,?)", (c["label"], c["tax"], c["unit"], c["hn"], c["hcm"], c["diff_pct"], c["basis"], ",".join(c["hn_ids"]), ",".join(c["hcm_ids"]), c["insight"]))
        for reg in ("hn", "hcm"):
            for q in ((c.get("parts") or {}).get(reg) or []): db.execute("insert into compare_parts values (?,?,?,?,?,?)", (c["label"], reg, q["id"], q["src"], q["raw"], q["norm"]))
    sup = J(os.path.join(D, "suppliers.json"), {"units": []}); n_fin = 0
    for u in sup["units"]:
        reg = u.get("reg") or {}; fin = u.get("fin"); fl = (u.get("flags") or []) + ((fin or {}).get("flags") or [])
        db.execute("insert into suppliers values (" + ",".join("?" * 24) + ")", (u["id"], u.get("org"), u.get("name"), u.get("short"), u.get("group"), u.get("website"), u.get("mst"), 1 if u.get("listed") else 0, u.get("ticker"), u.get("exchange"),
            reg.get("legal"), reg.get("address"), reg.get("status"), None if reg.get("active") is None else (1 if reg.get("active") else 0), reg.get("fetched"), reg.get("url"), 1 if fin else 0,
            ((fin or {}).get("label") or {}).get("label"), ((fin or {}).get("label") or {}).get("pts"), 1 if any(f.get("t") == "Tên pháp nhân cần xác nhận" for f in fl) else 0,
            " | ".join(f.get("t", "") for f in fl) or None, " | ".join(f"{f.get('t','')}: {f.get('d','')}" for f in fl) or None, u.get("note"), u.get("hub_note")))
        for per in (fin or {}).get("periods", []):
            v = per.get("v") or {}; n_fin += 1; src = per.get("source") or {}
            db.execute("insert into supplier_fin values (" + ",".join("?" * 28) + ")", (u["id"], per["id"], per.get("label"), per.get("start"), per.get("end"), per.get("months"), per.get("audit"), fin.get("basis"), src.get("title"), src.get("url"),
                *[v.get(k) for k in ("rev", "cogs", "gp", "fin_inc", "pbt", "np", "ta", "ca", "cl", "liab", "eq", "ar", "inv", "cash", "sti", "debt_st", "debt_lt", "cfo")]))
    news = []
    for x in (J(os.path.join(D, "market.json"), {"items": []})["items"]):
        s = x.get("sources") or [{}]; news.append((x["id"], "market", x["date"], x["title"], x.get("segment"), x.get("region"), x.get("summary"), x.get("takeaway"), ",".join(x.get("tax") or []), s[0].get("name"), s[0].get("url"), " ".join(q.get("url", "") for q in x.get("sources") or []), None))
    for x in (J(os.path.join(D, "legal.json"), {"items": []})["items"]):
        s = x.get("sources") or [{}]; news.append((x["id"], "legal", x.get("issued"), x["title"], x.get("kind"), None, x.get("summary"), x.get("impact"), None, s[0].get("name"), s[0].get("url"), " ".join(q.get("url", "") for q in x.get("sources") or []),
                                                   f"số hiệu {x.get('number')}; hiệu lực {x.get('effective')}; {x.get('status')}"))
    scm = J(os.path.join(D, "scm.json"), {"categories": []})
    for c in scm.get("categories", []):
        s = c.get("sources") or [{}]; news.append(("scm-" + c["id"], "scm", scm.get("updated"), f"{c['name']}: {c.get('headline')}", c.get("signal"), None, " · ".join((c.get("supply") or [])[:1] + (c.get("demand") or [])[:1]), c.get("timing"), ",".join(c.get("tax") or []),
                                                   s[0].get("name"), s[0].get("url"), " ".join(q.get("url", "") for q in c.get("sources") or []), f"xu hướng giá: {c.get('trend')}; nguồn mua đề xuất: {c.get('rec')}"))
    for x in (J(os.path.join(D, "trends.json"), {"items": []})["items"]):
        s = x.get("sources") or [{}]; news.append((x["id"], "trend", x["date"], x["title"], x.get("category"), x.get("region"), x.get("summary"), x.get("why"), ",".join(x.get("tax") or []), s[0].get("name"), s[0].get("url"), " ".join(q.get("url", "") for q in x.get("sources") or []), f"điểm {x.get('score')}"))
    db.executemany("insert into news values (" + ",".join("?" * 13) + ")", [tuple(nfc(v) for v in r) for r in news])
    counts = {t: db.execute(f"select count(*) from {t}").fetchone()[0] for t in ("taxonomy", "items", "prices_latest", "price_history", "compare_hn_hcm", "compare_parts", "suppliers", "supplier_fin", "news")}
    meta = [("generated_at", now), ("build_commit", sha), ("schema_version", "1"), ("hub_url", BASE), ("hub_built", hub.get("built")), ("prices_updated_at", prices.get("updated_at")), ("usd_vnd", str(hub.get("usd_vnd"))), ("timezone", "Asia/Ho_Chi_Minh (+07:00)"),
            ("refresh", "tự sinh lại sau mỗi lần CI (5 lần/ngày: 06:05, 09:05, 12:05, 15:05, 18:05 giờ VN, và sau mỗi lần cập nhật code)"), ("notes", "Giá tham khảo từ báo giá/nguồn công khai, không phải chào giá. Đọc llms.txt trước.")] + [(f"rows.{k}", str(v)) for k, v in counts.items()]
    db.executemany("insert into meta values (?,?)", [(k, nfc(v)) for k, v in meta]); db.commit(); db.execute("vacuum"); db.close(); os.replace(tmp, dbp)
    # ---- robots, sitemap
    open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8").write(f"# generated_at: {now}\nUser-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n")
    pages = sorted(os.path.basename(p) for p in glob.glob(os.path.join(SITE, "*.html"))); lm = now[:10]
    data_files = ["llms.txt", "prices.csv", "hub.sqlite", "lich-su-gia.csv", "bang-gia.csv", "prices.json", "forecast.json"] + sorted({"data/" + os.path.basename(p) for p in glob.glob(os.path.join(D, "*.json")) if os.path.basename(p) not in ("site-config.json",)} | {"data/landed-cost.json"})
    urls = [BASE + ("" if p == "index.html" else p) for p in pages] + [BASE + p for p in data_files if os.path.exists(os.path.join(SITE, p)) or p in ("llms.txt", "data/landed-cost.json")]
    open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write('<?xml version="1.0" encoding="UTF-8"?>\n<!-- generated_at: ' + now + ' -->\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{u}</loc><lastmod>{lm}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    # ---- llms.txt
    open(os.path.join(SITE, "llms.txt"), "w", encoding="utf-8").write(nfc(llms_text(now, sha, hub, prices, counts, dbp, pages)))
    print(f"aidata: {len(csv_rows)} mã, hub.sqlite {os.path.getsize(dbp)/1e6:.2f} MB {counts}, {time.time()-t0:.1f}s")
def size(p):
    p = os.path.join(SITE, p); return os.path.getsize(p) if os.path.exists(p) else None
def kb(n): return "?" if n is None else (f"{n/1e6:.1f} MB" if n >= 1e6 else f"{n/1e3:.0f} KB")
def llms_text(now, sha, hub, prices, counts, dbp, pages):
    cols = ""
    db = sqlite3.connect(dbp)
    for (t,) in db.execute("select name from sqlite_master where type='table' and name!='meta' order by rowid").fetchall() + [("meta",)]:
        cols += f"\n### {t} ({counts.get(t, db.execute(f'select count(*) from {t}').fetchone()[0])} dòng)\n" + "".join(f"- {r[1]} ({r[2] or 'text'}): {COLDOC.get(t, {}).get(r[1], '??')}\n" for r in db.execute(f"pragma table_info({t})"))
    db.close()
    ids = [x['id'] for x in hub['items']]; EX_ID = 'rmc_hcm_mk_m400' if 'rmc_hcm_mk_m400' in ids else ids[0]
    fl = "".join("- " + " · ".join(BASE + q for q in p.split(" · ")) + f" — {d.replace('{EX}', BASE + 'history/' + EX_ID + '.json')}" + (f" [{kb(size(p))}]" if size(p) else "") + "\n" for p, d in FILES_DOC)
    sql = "".join(f"\n{i}) {q}\n```sql\n{s}\n```\n" for i, (q, s) in enumerate(SQL_EX, 1))
    n_new = sum(1 for x in hub["items"] if (x.get("n_hist") or 0) < 2)
    import collections; fds = [x.get('first_date') for x in hub['items'] if x.get('first_date')]; fd_min, fd_max = min(fds), max(fds); fd_top = ', '.join(f'{d} ({n} mã)' for d, n in collections.Counter(fds).most_common(3))
    return f"""generated_at: {now} (build commit {sha}; hub.json built {hub.get('built')}; giá cập nhật {prices.get('updated_at')})
# Masterise Construction SCM Hub — dữ liệu giá vật tư & thị trường xây dựng (hướng dẫn cho AI)

> Hub tĩnh (GitHub Pages) tổng hợp giá vật tư xây dựng, thị trường, nhà thầu/nhà cung cấp, pháp lý cho đội Mua sắm – Đấu thầu của Masterise. URL gốc: {BASE}. Tất cả dữ liệu dưới đây là dữ liệu ĐÃ công khai trên hub.
> English: a static, public data hub of Vietnamese construction-material prices (Hanoi vs HCMC, world metals), market news, supplier registry/financials and legal updates. Start with prices.csv (latest price per item) or hub.sqlite (SQL). Prices are reference quotes from public sources, NOT supplier offers. Read section 5 (conventions) before comparing numbers.

## 1. Cập nhật khi nào
- Hub tự dựng lại 5 lần/ngày (06:05, 09:05, 12:05, 15:05, 18:05 giờ Việt Nam, UTC+7) và sau mỗi lần sửa code; mọi file ở gốc (llms.txt, prices.csv, hub.sqlite, sitemap.xml) sinh lại cùng lượt. 'Mới nhất' = lần dựng gần nhất: xem dòng generated_at ở đầu file này, cột generated_at của prices.csv hoặc bảng meta.
- Mỗi mã có ngày giá riêng (as_of) vì nguồn khác nhau: giá thế giới theo ngày/giờ; công bố Sở Xây dựng theo tháng/quý; báo giá nhà cung cấp theo ngày hub đọc được. Luôn đối chiếu as_of; stale=1 là dữ liệu cũ.
- Hiện có {len(hub['items'])} mã giá ({sum(1 for x in hub['items'] if x.get('grp')=='vn')} Việt Nam, {sum(1 for x in hub['items'] if x.get('grp')=='world')} thế giới). Độ dài lịch sử KHÁC NHAU theo mã: điểm đầu tiên (first_date) từ {fd_min} đến {fd_max}; ngày bắt đầu phổ biến nhất: {fd_top}. {n_new} mã đang 'mới thu' (<2 điểm).

## 2. Bắt đầu nhanh (khuyên dùng)
1. Câu hỏi về giá/biến động/so sánh vùng → {BASE}prices.csv (hoặc SQL trên {BASE}hub.sqlite).
2. Câu hỏi về 1 mã theo thời gian → {BASE}history/<item_id>.json hoặc bảng price_history.
3. Nhà cung cấp/nhà thầu → bảng suppliers + supplier_fin (hub.sqlite) hoặc {BASE}data/suppliers.json.
4. Tin/pháp lý/cung–cầu → bảng news (kind = market | legal | scm | trend).
5. Trang người dùng: {BASE} (trang chủ), {BASE}huong-dan.html (hướng dẫn). Mở mat-hang.html?id=<item_id> để đối chiếu một mã.

## 3. Danh sách file dữ liệu (URL cố định; [dung lượng lúc dựng])
{fl}
Trang HTML: {", ".join(pages)} (đều ở {BASE}). Mọi file ở trên là public; không có đăng nhập.

## 4. Ý nghĩa các cột/trường chính
### prices.csv (1 dòng/mã, {len(hub['items'])} dòng, UTF-8 không BOM, tiêu đề tiếng Anh snake_case, giá trị tiếng Việt)
- generated_at: thời điểm dựng file (ISO, +07:00), lặp ở mọi dòng.
- item_id, name: mã & tên mặt hàng (tên thường kèm nguồn trong ngoặc). group_site / group_subsite: nhóm cấp 1 / cấp 2 của hub (vd 'Xây dựng (phần thô)' / 'Bê tông thương phẩm'); group_master: nhóm giá master data (có thể rỗng); category: danh mục theo nguồn.
- region_label: vùng ghi trên nguồn; reg: hn (Hà Nội, Miền Bắc) | hcm (TP.HCM, Miền Nam) | vn (khu vực VN khác, vd Miền Trung) | world.
- source, source_url: nguồn & link; as_of: ngày giá của nguồn.
- price: giá; price_high: cận cao của khoảng giá nếu nguồn công bố khoảng (khi đó price là cận thấp; giá giữa = trung điểm); unit, currency: đơn vị và tiền tệ của price. vnd, vnd_unit: quy đổi VND (CHỈ hàng thế giới; tỷ giá Vietcombank chuyển khoản, chưa thuế/phí/vận chuyển; vnd_unit: VND/tấn với lb và short ton, VND/lượng với oz, còn lại VND/<đơn vị gốc>).
- conditions: ghi chú điều kiện giá nguyên văn từ nguồn (VAT, vận chuyển, bơm, ngày lấy báo giá…). vat_status: suy từ conditions ('chưa VAT' | 'đã gồm VAT' | 'không rõ' | 'không nêu'); slump: độ sụt trong tên bê tông; slump12_add: phụ phí tăng sụt do NCC công bố.
- d1_pct: % so với lần quan sát trước (hoặc % do nguồn tự cung cấp); w1_pct / mom_pct / yoy_pct: % so với điểm lịch sử gần nhất cách ~7 / ~30 / ~365 ngày (chỉ khi có điểm trong dung sai 40% khoảng cách đó, nếu không để trống); s0_pct: % từ ngày đầu thu (first_date) đến giá mới nhất, trống nếu <2 điểm.
- n_hist: số điểm lịch sử; is_new=1: 'mới thu' (<2 điểm, chưa có % thay đổi — KHÔNG phải giá không đổi); stale=1: dữ liệu cũ; mat_hang_url: trang chi tiết.
### data/hub.json
- Cùng dữ liệu với prices.csv ở items[] (id, name, unit, price, price_high, vnd, vnd_unit, as_of, src, url, stale, slump12_add, note=conditions, category, grp=vn|world, region, reg, tax=nhóm cấp 2, d1, w1, s0, mom, yoy, n_hist, spark = ≤90 điểm cuối chỉ khi ≥10 điểm, first_date, monthly=[{{m,p,chg}}] giá cuối tháng và % so tháng trước, mt/mt_conf = nhóm master data).
- compare[]: Hà Nội vs TP.HCM (label, unit, hn, hcm, diff_pct, insight, hn_ids, hcm_ids, basis, parts); steel_brand_pairs[]: cùng hãng thép hai miền; digest[]: tổng hợp theo tháng; mom_movers[]: id 12 mã biến động tháng lớn nhất; usd_vnd: tỷ giá.
### data/market.json, trends.json, legal.json, scm.json, suppliers.json: xem bảng news / suppliers / supplier_fin ở mục 7 (cùng trường, đã làm phẳng).

## 5. Quy ước hiểu số (đọc kỹ trước khi so sánh)
- Mọi giá là THAM KHẢO từ nguồn công khai/báo giá nhà cung cấp, KHÔNG phải chào giá chính thức; cần chào giá thực tế theo khối lượng, cự ly, thời điểm.
- Đơn vị: xem cột unit (VND/m³, VND/kg, VND/tấn, USD/tấn, USD/lb, USD/short ton = 907 kg…). Hàng thế giới quy đổi sang VND bằng tỷ giá Vietcombank chuyển khoản, chưa gồm thuế/phí/vận chuyển. Không cộng/so sánh khác đơn vị.
- VAT: hub KHÔNG tự cộng/trừ VAT trên giá niêm yết; điều kiện nằm ở conditions/vat_status (mỗi nguồn một kiểu: 'chưa VAT', 'đã gồm VAT 8%', 'không rõ'). Chỉ trong so sánh Hà Nội–TP.HCM cho bê tông (basis=rmc) hub mới quy về cơ sở chung.
- Bê tông tươi (cơ sở chung 'rmc'): quy về CHƯA VAT, độ sụt 12±2, CHƯA gồm bơm. Bảng giá đã gồm VAT được chia 1,08 (Mekong ghi rõ 8%; betonghanoi không ghi thuế suất nên hub GIẢ ĐỊNH 8%); bảng sụt 10±2 cộng phụ phí tăng sụt do chính NCC công bố (slump12_add; nếu NCC không công bố thì loại); loại betongdvc.com (không nêu sụt/VAT). Giá so sánh mỗi vùng = TRUNG VỊ các NCC sau quy đổi (xem compare_parts). Đây là giá niêm yết, cần chào giá thực tế.
- Hà Nội vs TP.HCM: diff_pct = (hcm/hn − 1)×100; dương = TP.HCM cao hơn. basis: rmc (bê tông, trung vị, cùng cơ sở); steel (thép, trung bình giá niêm yết nhà máy theo miền: Bắc ≈ Hà Nội, Nam ≈ TP.HCM); sxd (xi măng/cát/đá… HN = công bố giá Sở XD theo điểm giao cụ thể, HCM = bình quân/tại mỏ — KHÁC cơ sở, chỉ tham khảo xu hướng, đừng kết luận chênh giá).
- Tăng/giảm: ▲ tăng (bất lợi bên mua), ▼ giảm. Phần trăm là số học của hub từ lịch sử; lịch sử còn NGẮN (điểm đầu từ {fd_min} đến {fd_max} tuỳ mã) nên s0_pct/w1_pct chưa thể hiện xu hướng dài; so các mã với nhau phải xét first_date/n_hist.
- 'mới thu' (is_new=1): mã mới vào hub, chưa đủ 2 điểm → không có %/đường xu hướng; không được diễn giải là 'không đổi'.
- Ngày: ISO YYYY-MM-DD (múi giờ Việt Nam). Cùng 1 mã có thể không đổi giá nhiều ngày vì nguồn công bố định kỳ.
- Tin 'market' là tin biên tập có nguồn; cột takeaway/'hàm ý' là nhận định của người biên tập hub (không trích từ báo). Tin 'trend' có điểm 0–100 do hub chấm. Tin trong feed.json là tự động, chưa biên tập.

## 6. Giới hạn dữ liệu (đừng suy diễn quá)
- Không phải chào giá/hợp đồng; không có giá trúng thầu nội bộ; không có số nội bộ của Masterise.
- Nhà cung cấp/nhà thầu: hub chỉ có bản ghi thuế công khai (tên, mã số thuế, địa chỉ, tình trạng) và, với một số ít đơn vị, BCTC đã kiểm toán. has_fin=0 / nhãn 'Chưa có BCTC công khai' nghĩa là KHÔNG có số tài chính → không được ước đoán doanh thu/lợi nhuận. fin_label (Tốt/Theo dõi…) là nhãn SÀNG LỌC theo ngưỡng của hub, không phải xếp hạng tín nhiệm.
- Cờ 'Tên pháp nhân cần xác nhận' (name_needs_confirm=1) có HAI lý do, đọc ở flag_details: (a) tên trong danh sách theo dõi của hub khác tên trong bản ghi thuế; (b) hub chưa ghi tên pháp nhân, MST được chọn theo tên thương hiệu và khớp bản ghi thuế nhưng chưa có xác nhận từ hợp đồng/website. Cả hai đều cần đối chiếu hợp đồng/giấy phép đăng ký trước khi dùng tên. Số đơn vị có cờ thay đổi theo từng lần build: đếm bằng SQL, đừng dùng con số cố định.
- Dữ liệu xu hướng/dự báo là ước lượng thống kê; landed-cost, segments có số GIẢ ĐỊNH/ƯỚC TÍNH ghi rõ nhãn – chỉ dùng kèm nhãn.
- Nguồn có thể lỗi/chậm: kiểm stale, as_of, và mở source_url để đối chiếu.

## 7. hub.sqlite — cách dùng và lược đồ ({kb(size('hub.sqlite'))}, SQLite 3, UTF-8)
Tải {BASE}hub.sqlite rồi mở bằng sqlite3/DuckDB/pandas (pandas.read_sql_query). Bảng meta có generated_at, build_commit, số dòng từng bảng. Khóa: items.id = prices_latest.item_id = price_history.item_id. Số dòng lúc dựng: {', '.join(f'{k}={v}' for k, v in counts.items())}.
{cols}
## 8. SQL mẫu (đã chạy thử khi QA)
{sql}
## 9. Câu hỏi mẫu → file nên dùng
- "Giá bê tông M400 ở TP.HCM hôm nay, điều kiện gì?" → prices_latest + items (vat_status, slump, conditions) hoặc prices.csv lọc name chứa 'Bê tông tươi M400' & reg=hcm; so sánh quy cơ sở: compare_hn_hcm.
- "Hà Nội và TP.HCM bên nào rẻ hơn với thép/bê tông?" → compare_hn_hcm (đọc basis và insight trước khi kết luận).
- "Mã nào tăng nhiều nhất từ 22/10?" → SQL mẫu số 3 (so giá từ ngày đó với giá mới nhất bằng price_history); s0_pct (SQL số 4) là % từ NGÀY ĐẦU THU của chính mã nên chỉ trùng 22/10 với mã bắt đầu thu từ ngày đó. Loại is_new=1.
- "Nhà cung cấp X có BCTC công khai không / doanh thu bao nhiêu?" → suppliers.has_fin, supplier_fin; nếu has_fin=0 trả lời 'chưa có BCTC công khai'.
- "Đơn vị nào cần xác nhận tên pháp nhân?" → suppliers.name_needs_confirm=1.
- "Tin nhân công/chính sách gần đây ảnh hưởng mua sắm thế nào?" → news kind='market' (segment 'Nhân công', 'Chính sách') cột takeaway; văn bản pháp luật: kind='legal'.
- "Giá một mã biến động ra sao theo ngày?" → price_history hoặc history/<mã>.json.
- "Tín hiệu cung–cầu nhóm thép/xi măng?" → news kind='scm' hoặc data/scm.json.
"""
if __name__ == "__main__":
    import sys; main(sys.argv[sys.argv.index("--site") + 1] if "--site" in sys.argv else None)
