#!/usr/bin/env python3
"""Fetch metals & construction material prices (world + Vietnam) into SQLite.
Never fabricates: failed source => item keeps last good value and is flagged stale."""
import re, json, sqlite3, datetime as dt, traceback, os, sys
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "prices.db")
TZ = ZoneInfo("Asia/Saigon")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
      "Accept-Language": "vi,en;q=0.8"}
LB_PER_T = 2204.62262
NOW = dt.datetime.now(TZ)

import unicodedata
def slug(t):
    t = unicodedata.normalize("NFKD", t.replace("đ", "d").replace("Đ", "D")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "_", t).strip("_")
def now_iso(): return dt.datetime.now(TZ).isoformat(timespec="seconds")
def get(url, **kw):
    r = requests.get(url, headers=UA, timeout=30, **kw); r.raise_for_status(); return r

def num(s, dec=","):
    """Parse number. dec=',' means ',' thousands -> '1,234.5'; dec='.' means VN style '1.234,5'."""
    s = s.strip().replace("\xa0", "")
    if dec == ".":   # VN style: '.' thousands, ',' decimal
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", "")
    m = re.search(r"-?\d+(\.\d+)?", s)
    if not m: raise ValueError(f"no number in {s!r}")
    return float(m.group())

def item(id, group, category, name, unit, currency, price, src, url, as_of=None, **kw):
    d = dict(id=id, grp=group, category=category, name=name, unit=unit, currency=currency,
             price=price, src=src, url=url, as_of=as_of or NOW.date().isoformat())
    d.update(kw); return d

# ---------------- sources ----------------
def src_vcb():
    url = "https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx"
    x = get(url).text
    out = []
    for code in ["USD", "EUR", "CNY"]:
        m = re.search(r'CurrencyCode="%s"[^>]*Buy="([^"]*)"[^>]*Transfer="([^"]*)"[^>]*Sell="([^"]*)"' % code, x)
        if not m: continue
        buy, tr, sell = [num(v) if v.strip() not in ("-", "") else None for v in m.groups()]
        out.append(item(f"fx_{code.lower()}_vnd", "vn", "Tỷ giá", f"{code}/VND Vietcombank (chuyển khoản)",
                        f"VND/{code}", "VND", tr or buy, "Vietcombank", "https://www.vietcombank.com.vn/vi-VN/KHCN/Cong-cu-Tien-ich/Ty-gia",
                        note=f"Mua {buy:,.0f} · Bán {sell:,.0f}" if buy and sell else None, sell=sell))
    if not out: raise RuntimeError("VCB XML parse failed")
    return out

YF = [  # ticker, id, name, category, unit, convert-to-ton factor
    ("HG=F", "yf_copper", "Đồng (COMEX Copper HG)", "Kim loại màu", "USD/lb", None),
    ("ALI=F", "yf_aluminium", "Nhôm (COMEX Aluminum)", "Kim loại màu", "USD/tấn", None),
    ("HRC=F", "yf_hrc", "Thép cuộn cán nóng HRC (CME US Midwest)", "Thép & quặng", "USD/short ton", None),
    ("TIO=F", "yf_ironore", "Quặng sắt 62% Fe (SGX/CME TIO)", "Thép & quặng", "USD/tấn", None),
    ("GC=F", "yf_gold", "Vàng (COMEX Gold)", "Kim loại quý", "USD/oz", None),
    ("SI=F", "yf_silver", "Bạc (COMEX Silver)", "Kim loại quý", "USD/oz", None),
]
def src_yahoo():
    import yfinance as yf
    out = []
    for t, id, name, cat, unit, _ in YF:
        try:
            h = yf.Ticker(t).history(period="3mo", interval="1d").dropna(subset=["Close"])
            if len(h) == 0: continue
            last, prev = float(h["Close"].iloc[-1]), (float(h["Close"].iloc[-2]) if len(h) > 1 else None)
            d = h.index[-1].date().isoformat()
            out.append(item(id, "world", cat, name, unit, "USD", last, "Yahoo Finance (" + t + ")",
                            f"https://finance.yahoo.com/quote/{t}", as_of=d,
                            change_pct=((last / prev - 1) * 100 if prev else None), prev=prev,
                            backfill=[(i.date().isoformat(), float(v)) for i, v in h["Close"].items()]))
        except Exception as e:
            print("yahoo", t, e, file=sys.stderr)
    if not out: raise RuntimeError("Yahoo returned nothing")
    return out

WM_MAP = {"Copper": ("lme_copper", "Đồng", "Cu"), "Tin": ("lme_tin", "Thiếc", "Sn"), "Lead": ("lme_lead", "Chì", "Pb"),
          "Zinc": ("lme_zinc", "Kẽm", "Zn"), "Aluminium": ("lme_aluminium", "Nhôm", "Al"), "Nickel": ("lme_nickel", "Niken", "Ni")}
def wm_history(sym, n=90):
    url = f"https://www.westmetall.com/en/markdaten.php?action=table&field=LME_{sym}_cash"
    s = BeautifulSoup(get(url).content, "html.parser"); out = []
    for tr in s.select("tr"):
        c = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        try: out.append((dt.datetime.strptime(c[0], "%d. %B %Y").date().isoformat(), num(c[1])))
        except Exception: continue
        if len(out) >= n: break
    return out
def src_westmetall():
    url = "https://www.westmetall.com/en/markdaten.php"
    s = BeautifulSoup(get(url).content, "html.parser")
    out, as_of, section = [], None, None
    for tr in s.select("tr"):
        c = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if not c: continue
        if c[0].startswith("Official LME-Prices"):
            section = "lme"; as_of = dt.datetime.strptime(c[1], "%d. %B %Y").date().isoformat(); continue
        if c[0].startswith("LME Stocks") or c[0].startswith("Exchange"): section = None
        if c[0].startswith("Precious Metals"):
            section = "pm"; pm_date = dt.datetime.strptime(c[1], "%d. %B %Y").date().isoformat(); continue
        if section == "lme" and c[0] in WM_MAP:
            id, vn, sym = WM_MAP[c[0]]
            try: bf = wm_history(sym)
            except Exception as e: bf = []; print("wm hist", sym, e, file=sys.stderr)
            prev = next((p for d, p in bf if d < as_of), None)
            out.append(item(id, "world", "Kim loại màu", f"{vn} LME – giá chính thức (Cash)", "USD/tấn", "USD",
                            num(c[1]), "Westmetall (LME official prices)", url, as_of=as_of,
                            note=f"3 tháng: {c[2]} USD/t", prev=prev,
                            change_pct=((num(c[1]) / prev - 1) * 100 if prev else None), backfill=bf))
        if section == "pm" and c[0].startswith("Gold London Fixing"):
            out.append(item("lbma_gold", "world", "Kim loại quý", "Vàng London Fixing (LBMA)", "USD/oz", "USD",
                            num(c[1]), "Westmetall (LBMA)", url, as_of=pm_date, prev=num(c[2])))
    if len(out) < 4: raise RuntimeError("Westmetall parse failed")
    return out

TE_MAP = {"Steel": ("te_rebar_shfe", "Thép cây (SHFE Rebar)", "Thép & quặng"),
          "HRC Steel": ("te_hrc", "Thép HRC (tham chiếu TE)", "Thép & quặng"),
          "Iron Ore": ("te_ironore", "Quặng sắt 62% Fe", "Thép & quặng"),
          "Iron Ore CNY": ("te_ironore_cny", "Quặng sắt (DCE, CNY)", "Thép & quặng"),
          "Scrap Steel": ("te_scrap", "Thép phế liệu", "Thép & quặng"),
          "Coking Coal": ("te_cokingcoal", "Than cốc luyện kim", "Thép & quặng"),
          "Copper": ("te_copper", "Đồng (TE)", "Kim loại màu"),
          "Aluminum": ("te_aluminium", "Nhôm (TE/LME)", "Kim loại màu"),
          "Zinc": ("te_zinc", "Kẽm (TE/LME)", "Kim loại màu"), "Nickel": ("te_nickel", "Niken (TE/LME)", "Kim loại màu"),
          "Lead": ("te_lead", "Chì (TE/LME)", "Kim loại màu"), "Tin": ("te_tin", "Thiếc (TE/LME)", "Kim loại màu")}
def src_te():
    url = "https://tradingeconomics.com/commodities"
    s = BeautifulSoup(get(url).content, "html.parser")
    out = []
    for tr in s.select("table tr"):
        c = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if len(c) < 4: continue
        m = re.match(r"(.+?)\s+([A-Z]{3}/[A-Za-z.]+)$", c[0])
        if not m or m.group(1) not in TE_MAP: continue
        id, name, cat = TE_MAP[m.group(1)]
        cur, u = m.group(2).split("/")
        unit = {"T": "tấn", "Lbs": "lb", "t.oz": "oz"}.get(u, u)
        try: pct = float(c[3].replace("%", ""))
        except: pct = None
        out.append(item(id, "world", cat, name, f"{cur}/{unit}", cur, num(c[1]), "Trading Economics",
                        "https://tradingeconomics.com/commodities", change_pct=pct,
                        note="Giá tham khảo theo thời gian thực (có thể trễ)"))
    if len(out) < 4: raise RuntimeError("TE parse failed")
    return out

def src_sjc():
    url = "https://giavang.org/trong-nuoc/sjc/"
    s = BeautifulSoup(get(url).content, "html.parser")
    out = []
    for tr in s.select("table tr"):
        c = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        name = c[-3] if len(c) >= 3 else ""
        if name.startswith("Vàng SJC 1L") and "sjc_bar" not in [o["id"] for o in out]:
            buy, sell = num(c[-2], "."), num(c[-1], ".")
            out.append(item("sjc_bar", "vn", "Vàng trong nước", "Vàng miếng SJC 1L-10L (giá bán ra)", "VND/lượng", "VND",
                            sell * 1000, "giavang.org (giá SJC)", url, note=f"Mua vào {buy*1000:,.0f}", buy=buy*1000))
        if name.startswith("Vàng nhẫn SJC 99,99% 1 chỉ") and "sjc_ring" not in [o["id"] for o in out]:
            buy, sell = num(c[-2], "."), num(c[-1], ".")
            out.append(item("sjc_ring", "vn", "Vàng trong nước", "Vàng nhẫn SJC 99,99% (giá bán ra)", "VND/lượng", "VND",
                            sell * 1000, "giavang.org (giá SJC)", url, note=f"Mua vào {buy*1000:,.0f}", buy=buy*1000))
    if not out: raise RuntimeError("SJC parse failed")
    return out

def src_sjc_check():
    """Second source for SJC (webgia.com, per chỉ) – used for cross-check only."""
    url = "https://webgia.com/gia-vang/sjc/"
    s = BeautifulSoup(get(url).content, "html.parser")
    for tr in s.select("table tr"):
        c = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if len(c) >= 3 and c[-3].startswith("Vàng SJC 1L"):
            return [item("sjc_bar_webgia", "vn", "Vàng trong nước", "Vàng miếng SJC (đối chiếu webgia.com)", "VND/lượng", "VND",
                         num(c[-1], ".") * 10, "webgia.com", url, hidden=1)]
    raise RuntimeError("webgia parse failed")

STEEL_COLS = {"CB240 D6 (cuộn)": ("D6", 4), "CB300 D10": ("D10", 5), "CB400 D16": ("D16", 7), "CB500 D16": ("D16", 9)}
def src_steelonline():
    url = "https://steelonline.vn/price-list"
    s = BeautifulSoup(get(url).content, "html.parser")
    m = re.search(r"NGÀY\s+(\d{2})-(\d{2})-(\d{4})", s.get_text(" "))
    as_of = f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None
    out = []
    for blk in s.select("div.img-case.tabs"):
        h = blk.select_one(".branch-title")
        if not h: continue
        brand = h.get_text(strip=True).replace("BẢNG GIÁ THÉP", "").strip().replace("Thép VAS", "VAS")
        regions = {a.get("data-tab-id"): a.get_text(strip=True) for a in blk.select(".tabs-header a[data-tab-id]")}
        for tab in blk.select("div.tabs-content > div.tab"):
            region = regions.get(tab.get("data-tab-id"), "")
            t = tab.find("table")
            if not t: continue
            rows = {}
            for tr in t.select("tr"):
                c = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
                if len(c) >= 11 and re.match(r"D\d+", c[1]): rows[c[1]] = c
            for label, (dia, col) in STEEL_COLS.items():
                r = rows.get(dia)
                if not r or r[col] in ("-", "", "0"): continue
                try: p = num(r[col], ".")
                except ValueError: continue
                if p <= 0: continue
                sid = slug(brand + " " + region + " " + label)
                out.append(item("vnsteel_" + sid, "vn", "Thép xây dựng", f"Thép {brand} {label}", "VND/kg", "VND", p,
                                "steelonline.vn", url, as_of=as_of, region=region, brand=brand,
                                note="Giá tham khảo đại lý, chưa VAT & vận chuyển"))
    if len(out) < 5: raise RuntimeError("steelonline parse failed")
    return out

TTHH = [("gia-xi-mang-hom-nay", "Xi măng"), ("gia-cat-xay-dung-hom-nay", "Cát"),
        ("gia-da-xay-dung-hom-nay", "Đá xây dựng"), ("gia-gach-xay-dung-hom-nay", "Gạch xây")]
def src_tthh():
    out, errs = [], []
    for pslug, cat in TTHH:
        url = f"https://www.thitruonghanghoa.com/gia-ca-thi-truong-viet-nam/{pslug}"
        try:
            lines = BeautifulSoup(get(url).content, "html.parser").get_text("\n", strip=True).split("\n")
            i = lines.index("Giá ngày")
            d, meta = lines[i + 1], lines[i + 2]
            as_of = dt.datetime.strptime(d, "%d/%m/%Y").date().isoformat()
            loc = re.search(r"tại\s+([^·]+)", meta); unitm = re.search(r"đơn vị\s+([^\s·]+)", meta)
            loc = loc.group(1).strip() if loc else ""; unit = unitm.group(1) if unitm else ""
            j = lines.index("So với phiên trước", i) + 1
            while j + 1 < len(lines) and not lines[j].startswith("Giá tham khảo"):
                name, val = lines[j], lines[j + 1]
                chg = lines[j + 2] if j + 2 < len(lines) else "—"
                nums = re.findall(r"\d[\d.]*", val)
                if not nums: break
                lo = num(nums[0], "."); hi = num(nums[1], ".") if len(nums) > 1 else None
                try: pct = float(chg.replace("%", "").replace(",", ".").replace("+", "")) if "%" in chg else None
                except ValueError: pct = None
                sid = slug(cat + " " + name)
                out.append(item("vnmat_" + sid, "vn", cat, name, unit.replace("đ", "VND"), "VND", lo,
                                "thitruonghanghoa.com (tổng hợp công bố giá Sở XD)", url, as_of=as_of,
                                price_high=hi, region=loc, change_pct=pct,
                                note="Giá công bố định kỳ (tháng), chưa VAT"))
                j += 3
        except Exception as e:
            errs.append(f"{pslug}: {e}")
    if errs: print("tthh errors", errs, file=sys.stderr)
    snap = os.path.join(BASE, "data", "tthh_snapshot.json")
    if out and not errs:
        old = json.load(open(snap, encoding="utf-8"))["items"] if os.path.exists(snap) else None
        if old != out:
            json.dump({"saved_at": now_iso(), "items": out}, open(snap, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    if not out or errs:
        # e.g. site blocks GitHub runner IPs: fall back to the snapshot relayed from the always-on box
        if os.path.exists(snap):
            d = json.load(open(snap, encoding="utf-8"))
            for r in d["items"]:
                r["note"] = (r.get("note") or "") + f" · lấy qua bản chụp lúc {d['saved_at'][:16].replace('T', ' ')} (nguồn chặn máy chủ GitHub)"
                r["src"] = r["src"].split(" [")[0] + " [relay]"
            have = {r["id"] for r in out}
            out += [r for r in d["items"] if r["id"] not in have]
            print("tthh: using snapshot", d["saved_at"], file=sys.stderr)
        if not out: raise RuntimeError("; ".join(errs))
    return out

def src_hanoi_static():
    p = os.path.join(BASE, "hanoi_sxd_q3_2026.json")
    data = json.load(open(p, encoding="utf-8"))
    return [item(**d) for d in data]

SOURCES = [("Vietcombank", src_vcb), ("Westmetall/LME", src_westmetall), ("Yahoo Finance", src_yahoo),
           ("Trading Economics", src_te), ("SJC (giavang.org)", src_sjc), ("SJC (webgia đối chiếu)", src_sjc_check),
           ("steelonline.vn", src_steelonline), ("thitruonghanghoa.com", src_tthh),
           ("Sở XD Hà Nội Q3/2026 (tĩnh)", src_hanoi_static)]

# Nguồn bổ sung (bê tông thương phẩm, nhựa PE/PVC/PP, ống HDPE) – module forecast/sources.py
try:
    from forecast.sources import NEW_SOURCES
    SOURCES += NEW_SOURCES
except Exception as _e:
    print("forecast.sources not loaded:", _e, file=sys.stderr)

SCHEMA = """
create table if not exists items(id text primary key, meta text, last_ok text, last_try text, status text);
create table if not exists obs(id text, fetched_at text, as_of text, price real, price_high real, change_pct real,
  primary key(id, fetched_at));
create table if not exists runs(source text, fetched_at text, ok int, n int, error text);
"""
def main():
    con = sqlite3.connect(DB); con.executescript(SCHEMA)
    ts = now_iso(); seen = set()
    for name, fn in SOURCES:
        try:
            if name in os.environ.get("SIMULATE_FAIL", "").split(","): raise RuntimeError("simulated failure (test)")
            rows = fn()
            for r in rows:
                seen.add(r["id"])
                for d, p in r.pop("backfill", None) or []:
                    con.execute("insert or ignore into obs values(?,?,?,?,?,?)", (r["id"], d + "T00:00:00+07:00", d, p, None, None))
                con.execute("insert or replace into items(id,meta,last_ok,last_try,status) values(?,?,?,?, 'ok')",
                            (r["id"], json.dumps(r, ensure_ascii=False), ts, ts))
                con.execute("insert or replace into obs values(?,?,?,?,?,?)",
                            (r["id"], ts, r.get("as_of"), r["price"], r.get("price_high"), r.get("change_pct")))
            con.execute("insert into runs values(?,?,?,?,?)", (name, ts, 1, len(rows), None))
            print(f"OK   {name}: {len(rows)} items")
        except Exception as e:
            con.execute("insert into runs values(?,?,?,?,?)", (name, ts, 0, 0, f"{type(e).__name__}: {e}"[:500]))
            print(f"FAIL {name}: {e}")
    # mark items not refreshed in this run as stale (keeps last good value)
    for (iid,) in con.execute("select id from items").fetchall():
        if iid not in seen:
            con.execute("update items set status='stale', last_try=? where id=?", (ts, iid))
    con.commit(); con.close()

if __name__ == "__main__":
    main()
