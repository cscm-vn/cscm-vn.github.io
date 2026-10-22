#!/usr/bin/env python3
"""Xây dựng dự báo 3/6/12 tháng -> <site>/forecast.json (+ copy forecast.html).
Chạy SAU fetcher.py và export_static.py:  python forecast/build.py [--site site] [--db data/prices.db]
Dữ liệu thật: World Bank Pink Sheet (tháng), Yahoo Finance (tháng + đường cong futures), Westmetall/LME (DB), TE (DB/trang),
giá VN trong data/prices.db + nguồn bổ sung forecast/sources.py. Không bịa số: chuỗi thiếu => bỏ qua/ghi chú."""
import os, sys, json, math, shutil, argparse, warnings, datetime as dt, sqlite3, re
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd, requests
warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from forecast import sources as S
TZ = ZoneInfo("Asia/Saigon"); NOW = dt.datetime.now(TZ)
H = [3, 6, 12]; LB = 2204.62262
PINK_URL = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"

# ---------------- data ----------------
def pink():
    p = os.path.join(HERE, "raw", "pink.xlsx"); os.makedirs(os.path.dirname(p), exist_ok=True)
    if not os.path.exists(p) or (dt.datetime.now().timestamp() - os.path.getmtime(p)) > 7 * 86400:
        try:
            r = requests.get(PINK_URL, timeout=60); r.raise_for_status(); open(p, "wb").write(r.content)
        except Exception as e: print("pink sheet download failed (dùng bản cũ nếu có):", e)
    x = pd.read_excel(p, sheet_name="Monthly Prices", header=None)
    names = [str(v).strip() for v in x.iloc[4]]
    rows = x.iloc[6:]; idx = pd.to_datetime(rows[0].astype(str).str.replace("M", "-") + "-01", errors="coerce")
    out = {}
    for col, key in [("Copper", "copper"), ("Aluminum", "alu"), ("Iron ore, cfr spot", "ironore"),
                     ("Crude oil, Brent", "brent"), ("Coal, Australian", "coal")]:
        j = names.index(col); s = pd.to_numeric(rows[j], errors="coerce"); s.index = idx
        out[key] = s.dropna()
    return out

def yfm(t, mult=1.0):
    import yfinance as yf
    try:
        h = yf.Ticker(t).history(period="max", interval="1mo")["Close"].dropna()
        h.index = pd.to_datetime([d.strftime("%Y-%m-01") for d in h.index]); h = h[~h.index.duplicated(keep="last")]
        return h * mult
    except Exception as e:
        print("yf fail", t, e); return pd.Series(dtype=float)

def yflast(t):
    import yfinance as yf
    try:
        h = yf.Ticker(t).history(period="5d")["Close"].dropna(); return float(h.iloc[-1]) if len(h) else None
    except Exception: return None

def splice(wb, y):
    """Pink Sheet (dài) + Yahoo (gần đây): scale Yahoo về mức WB theo tỷ lệ TB các tháng chồng lấn."""
    if wb is None or not len(wb): return y
    if not len(y): return wb
    ov = wb.index.intersection(y.index)[-24:]
    k = float((wb[ov] / y[ov]).median()) if len(ov) >= 6 else 1.0
    return pd.concat([wb, y[y.index > wb.index[-1]] * k]).sort_index(), k

def db_items(db):
    c = sqlite3.connect(db); d = {}
    for i, m, st in c.execute("select id, meta, status from items"):
        m = json.loads(m); m["status"] = st; d[i] = m
    obs = {}
    for i, f, p in c.execute("select id, fetched_at, price from obs order by fetched_at"):
        obs.setdefault(i, []).append((f[:10], p))
    return d, obs

# ---------------- models ----------------
def fc_rw(y, h): return float(y.iloc[-1])
def fc_ets(y, h):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    m = ExponentialSmoothing(np.log(y.values), trend="add", damped_trend=True).fit()
    return float(np.exp(m.forecast(h)[-1]))
def fc_arima(y, h):
    from statsmodels.tsa.arima.model import ARIMA
    m = ARIMA(np.log(y.values), order=(1, 1, 0)).fit()
    return float(np.exp(m.forecast(h)[-1]))
def fc_arimax(y, h, x=None):
    """ARIMA(1,1,0) + biến ngoại sinh (Δlog Brent & Δlog USD index, trễ 1 tháng); tương lai: exog = 0 (đi ngang)."""
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    if x is None: return fc_arima(y, h)
    X = np.log(x).diff().shift(1).reindex(y.index).fillna(0)
    m = SARIMAX(np.log(y.values), exog=X.values, order=(1, 1, 0)).fit(disp=False)
    return float(np.exp(m.forecast(h, exog=np.zeros((h, X.shape[1])))[-1]))
METHODS = {"rw": fc_rw, "ets": fc_ets, "arima": fc_arima}

def ensemble(y, h, x=None):
    v = [fc_rw(y, h), fc_ets(y, h), fc_arima(y, h)]
    if x is not None:
        try: v.append(fc_arimax(y, h, x))
        except Exception: pass
    return float(np.exp(np.mean(np.log(v))))

def backtest(y, x=None, n=60, step=2):
    """Rolling-origin: dự báo từ mỗi gốc trong n tháng cuối; MAPE theo kỳ hạn & phương pháp."""
    res = {h: {k: [] for k in list(METHODS) + ["ens"]} for h in H}
    T = len(y)
    for o in range(T - n, T, step):
        tr = y.iloc[max(0, o - 180):o]
        xt = x.loc[:tr.index[-1]] if x is not None else None
        for h in H:
            if o + h - 1 >= T: continue
            act = y.iloc[o + h - 1]
            for k, f in METHODS.items():
                try: res[h][k].append(abs(f(tr, h) / act - 1))
                except Exception: pass
            try: res[h]["ens"].append(abs(ensemble(tr, h, xt) / act - 1))
            except Exception: pass
    return {h: {k: (round(100 * np.mean(v), 1) if v else None) for k, v in d.items()} | {"n": len(d["ens"])} for h, d in res.items()}

def qbands(y, since="2010-01-01"):
    """Biên độ thực nghiệm: phân vị P10/P90 của log-thay đổi h tháng (từ 2010)."""
    ly = np.log(y[y.index >= since]); out = {}
    for h in H:
        r = (ly.shift(-h) - ly).dropna()
        out[h] = (float(np.percentile(r, 10) - np.median(r)), float(np.percentile(r, 90) - np.median(r)), float(r.std()))
    return out

def mom_yoy(y):
    def ch(k): return round(100 * (y.iloc[-1] / y.iloc[-1 - k] - 1), 1) if len(y) > k else None
    return {"mom": ch(1), "qoq": ch(3), "yoy": ch(12)}

def conf_label(mape):
    if mape is None: return "Thấp"
    return "Cao" if mape < 4 else ("Trung bình" if mape < 9 else "Thấp")

# ---------------- build ----------------
TAX = {  # key -> id cấp 2 trong data/taxonomy.json (cây danh mục dùng chung toàn site)
 "copper": "mep.dong-nhom", "alu": "mep.dong-nhom", "cu_vnd": "mep.cap-dien", "al_vnd": "mep.dong-nhom", "idx_cable": "mep.cap-dien",
 "ironore": "xd.thep-ket-cau", "hrc": "xd.thep-ket-cau", "scrap": "xd.thep-ket-cau", "coking": "xd.thep-ket-cau",
 "rebar": "xd.cot-thep", "cement": "xd.xi-mang", "sand": "xd.cat-da", "stone": "xd.cat-da", "rmc250": "xd.be-tong", "rmc300": "xd.be-tong", "rmc400": "xd.be-tong",
 "pe": "mep.ong-nuoc", "pp": "mep.ong-nuoc", "pvc": "mep.ong-nuoc", "hdpe_pipe": "mep.ong-nuoc",
 "brent": "tt.nang-luong", "coal": "tt.nang-luong", "usdvnd": "tt.ty-gia",
 "idx_transformer": "mep.may-phat", "idx_elevator": "mep.thang-may", "idx_hvac": "mep.hvac", "idx_switchboard": "mep.tu-dien", "idx_genset": "mep.may-phat",
}
def tax_path(k, taxonomy):
    tid = TAX.get(k)
    for n in (taxonomy or {}).get("tree", []):
        for c in n["children"]:
            if c["id"] == tid: return [n["name"], c["name"]]
    return ["Khác"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--site", default=os.path.join(ROOT, "site"))
    ap.add_argument("--db", default=os.path.join(ROOT, "data", "prices.db")); a = ap.parse_args()
    taxonomy = None
    tp = os.path.join(ROOT, "data", "taxonomy.json")
    if os.path.exists(tp): taxonomy = json.load(open(tp, encoding="utf-8"))
    sys.path.insert(0, ROOT); import store; store.ensure_db(a.db) if os.path.abspath(a.db) == os.path.abspath(store.DB) else None
    items, obs = db_items(a.db)
    drivers = json.load(open(os.path.join(HERE, "drivers.json"), encoding="utf-8"))
    P = pink(); notes = []
    # --- monthly world series ---
    ser, src = {}, {}
    def put(k, s, label): ser[k] = s.dropna(); src[k] = label
    s, k = splice(P["copper"], yfm("HG=F", LB)); put("copper", s, f"World Bank Pink Sheet (Copper, LME) đến {P['copper'].index[-1]:%m/%Y} + COMEX HG=F (quy USD/t, hệ số nối {k:.3f})")
    s, k = splice(P["alu"], yfm("ALI=F")); put("alu", s, f"World Bank Pink Sheet (Aluminum) + COMEX ALI=F (hệ số nối {k:.3f})")
    s, k = splice(P["ironore"], yfm("TIO=F")); put("ironore", s, f"World Bank Pink Sheet (Iron ore cfr) + SGX/CME TIO=F (hệ số nối {k:.3f})")
    s, k = splice(P["brent"], yfm("BZ=F")); put("brent", s, f"World Bank Pink Sheet (Brent) + ICE Brent BZ=F (hệ số nối {k:.3f})")
    put("hrc", yfm("HRC=F") * 1.10231, "CME HRC=F (US Midwest), quy USD/tấn mét"); put("scrap", yfm("BUS=F") * 0.98421, "CME BUS=F (US busheling scrap), quy USD/tấn mét")
    put("coal", yfm("MTF=F"), "ICE Rotterdam Coal (API2) MTF=F"); put("usdvnd", yfm("VND=X"), "Yahoo VND=X (tham chiếu liên ngân hàng)")
    dxy = yfm("DX-Y.NYB")
    # override last point with today's DB (LME official) where available
    for k, iid, f in [("copper", "lme_copper", 1), ("alu", "lme_aluminium", 1), ("usdvnd", "fx_usd_vnd", 1)]:
        if iid in items and len(ser[k]):
            ser[k].iloc[-1] = items[iid]["price"] * f
    # futures curve
    def lme3m(iid):
        n = items.get(iid, {}).get("note") or ""; m = re.search(r"3 tháng: ([\d,\.]+)", n)
        return float(m.group(1).replace(",", "")) if m else None
    curves = {}
    hg = {c: yflast(c) for c in ["HG=F", "HGH27.CMX", "HGK27.CMX", "HGZ27.CMX"]}
    bz = {c: yflast(c) for c in ["BZ=F", "BZF27.NYM", "BZH27.NYM", "BZJ27.NYM", "BZZ27.NYM"]}
    al = {c: yflast(c) for c in ["ALI=F", "ALIZ26.CMX", "ALIH27.CMX", "ALIZ27.CMX"]}
    curves["copper"] = {"lme_cash": items.get("lme_copper", {}).get("price"), "lme_3m": lme3m("lme_copper"), "comex": hg}
    curves["alu"] = {"lme_cash": items.get("lme_aluminium", {}).get("price"), "lme_3m": lme3m("lme_aluminium"), "comex": al}
    curves["brent"] = {"ice": bz}
    def fut_pct(k, h):
        """% thay đổi hàm ý từ futures tại kỳ hạn h (None nếu không có)."""
        c = curves.get(k)
        if not c: return None
        if k in ("copper", "alu"):
            if h == 3 and c["lme_cash"] and c["lme_3m"]: return c["lme_3m"] / c["lme_cash"] - 1
            cm = c["comex"]; f0 = list(cm.values())[0]; f12 = list(cm.values())[-1]
            if f0 and f12 and h == 12: return f12 / f0 - 1
            if f0 and f12 and h == 6: return (f12 / f0 - 1) * 0.5
            return None
        if k == "brent":
            f0, f3, f6, f12 = bz.get("BZ=F"), bz.get("BZF27.NYM"), bz.get("BZH27.NYM") or bz.get("BZJ27.NYM"), bz.get("BZZ27.NYM")
            v = {3: f3, 6: f6, 12: f12}.get(h)
            return v / f0 - 1 if v and f0 else None
    # --- forecast world items ---
    W = {}
    for k in ["copper", "alu", "ironore", "hrc", "scrap", "brent", "coal", "usdvnd"]:
        y = ser[k]; y = y[y.index >= "2005-01-01"]
        if len(y) < 48: notes.append(f"{k}: lịch sử quá ngắn"); continue
        X = None
        if k in ("copper", "alu", "ironore"):
            X = pd.concat([ser["brent"], dxy], axis=1).dropna(); X.columns = ["brent", "dxy"]
            X = X.reindex(y.index).ffill()
        bt = backtest(y, X); qb = qbands(y)
        fc = {}
        for h in H:
            m = ensemble(y, h, X); fp = fut_pct(k, h)
            base = m if fp is None else math.exp(0.5 * math.log(m) + 0.5 * math.log(y.iloc[-1] * (1 + fp)))
            lo, hi, sd = qb[h]
            fc[h] = {"model": m, "futures": None if fp is None else y.iloc[-1] * (1 + fp), "base": base,
                     "lo": base * math.exp(lo), "hi": base * math.exp(hi), "sd": sd}
        W[k] = dict(y=y, bt=bt, fc=fc, trend=mom_yoy(y))
        print(f"{k:8s} now={y.iloc[-1]:.2f}  12M base={fc[12]['base']:.2f}  MAPE ens 3/6/12={bt[3]['ens']}/{bt[6]['ens']}/{bt[12]['ens']} rw={bt[3]['rw']}/{bt[6]['rw']}/{bt[12]['rw']}")
    def pct(k, h, field="base"): return W[k]["fc"][h][field] / W[k]["y"].iloc[-1] - 1
    def blend(weights, h, infl=0.0, idio=0.0):
        """% thay đổi của chỉ số chi phí: Σ w_i·%Δ_i + phần 'khác' tăng theo lạm phát; biên độ: tổ hợp sd + sai số riêng."""
        b = sum(w * pct(k, h) for k, w in weights.items()) + (1 - sum(weights.values())) * infl * h / 12
        sd = math.sqrt(sum((w * W[k]["fc"][h]["sd"]) ** 2 for k, w in weights.items()) + (idio * math.sqrt(h / 12)) ** 2)
        return b, sd
    INFL = 0.035  # giả định lạm phát chi phí 'khác' (nhân công, khấu hao, biên) ~3,5%/năm ≈ CPI VN gần đây – là GIẢ ĐỊNH, ghi rõ trên UI
    out_items = []
    def emit(key, group, name, region, unit, now, as_of, fc_pct, method, src_, conf, bt=None, trend=None, hist=None, drivers_k=None, pair=None, extra=None):
        f = {}
        for h in H:
            b, sd = fc_pct[h]
            f[str(h)] = {"base": now * (1 + b), "lo": now * (1 + b) * math.exp(-1.2816 * sd), "hi": now * (1 + b) * math.exp(1.2816 * sd), "pct": 100 * b}
        d = dict(id=key + ("_" + region if region else ""), key=key, group=group, name=name, region=region, unit=unit, now=now, as_of=as_of,
                 fc=f, method=method, src=src_, confidence=conf, backtest=bt, trend=trend, hist=hist, path=tax_path(key, taxonomy), tax=TAX.get(key), pair=pair)
        if extra: d.update(extra)
        out_items.append(d)
    def wfc(k):  # world fc -> (pct, sd) incl. empirical band -> convert lo/hi to sd-equivalent
        return {h: (pct(k, h), (math.log(W[k]["fc"][h]["hi"] / W[k]["fc"][h]["lo"])) / (2 * 1.2816)) for h in H}
    def hist(k, n=72): y = W[k]["y"].iloc[-n:]; return [[d.strftime("%Y-%m"), round(float(v), 4)] for d, v in y.items()]
    G = {"copper": "copper", "alu": "aluminium", "ironore": "ironore", "hrc": "steel_world", "scrap": "steel_world", "brent": "energy", "coal": "coal", "usdvnd": "fx"}
    NM = {"copper": ("Đồng LME (Cash)", "USD/tấn"), "alu": ("Nhôm LME (Cash)", "USD/tấn"), "ironore": ("Quặng sắt 62% Fe", "USD/tấn"),
          "hrc": ("Thép HRC (CME, US Midwest)", "USD/tấn"), "scrap": ("Thép phế (CME busheling)", "USD/tấn"), "brent": ("Dầu Brent", "USD/thùng"),
          "coal": ("Than nhiệt (ICE, Yahoo MTF=F)", "USD/tấn"), "usdvnd": ("Tỷ giá USD/VND", "VND/USD")}
    for k in W:
        bt = W[k]["bt"]
        meth = "Ensemble (Random walk + ETS damped + ARIMA(1,1,0)" + (" + ARIMAX[Brent, USD index]" if k in ("copper", "alu", "ironore") else "") + ")"
        if fut_pct(k, 3) is not None or fut_pct(k, 12) is not None: meth += " ⊕ 50% giá futures (LME 3M / COMEX / ICE)"
        emit(k, G[k], NM[k][0], None, NM[k][1], float(W[k]["y"].iloc[-1]), W[k]["y"].index[-1].strftime("%m/%Y"), wfc(k), meth, src[k],
             conf_label(bt[12]["ens"]) + " (12T)", bt, W[k]["trend"], hist(k), extra={"curve": curves.get(k)})
    # coking coal: current only
    if "te_cokingcoal" in items:
        it = items["te_cokingcoal"]
        out_items.append(dict(id="coking", key="coking", group="steel_world", name="Than cốc luyện kim", region=None, unit="USD/tấn", now=it["price"],
                              as_of=it.get("as_of"), fc=None, method="Không có lịch sử miễn phí đủ dài → chỉ hiển thị giá & động lực", src="Trading Economics",
                              confidence="—", path=tax_path("coking", taxonomy), tax=TAX.get("coking"), trend={"mom": 0.38, "yoy": 36.76, "src": "TE 21/10/2026"}))
    # ---- VN steel (pass-through) ----
    # Chi phí thép thanh lò cao/lò điện: quặng (~1,6t), than cốc, phế; giá VN thực tế bám chậm & ít biến động hơn đầu vào.
    # β pass-through 0,45 trên chỉ số đầu vào quy VND (giả định, đối chiếu: VN rebar 2021–2025 dao động ~±25%/năm khi quặng ±50%).
    def vn_steel_pct():
        r = {}
        for h in H:
            b_in, sd_in = blend({"ironore": 0.45, "scrap": 0.35, "hrc": 0.20}, h)
            b_fx = pct("usdvnd", h)
            b = 0.45 * b_in + 0.6 * b_fx; sd = math.sqrt((0.45 * sd_in) ** 2 + (0.04 * math.sqrt(h / 12)) ** 2)
            r[h] = (b, sd)
        return r
    vs = vn_steel_pct()
    for reg, lbl, rname in [("mien_bac", "Hà Nội / Miền Bắc", "HN"), ("mien_nam", "TP.HCM / Miền Nam", "HCM")]:
        ps = {i: m["price"] for i, m in items.items() if i.startswith("vnsteel_") and f"_{reg}_cb300_d10" in i}
        if not ps: continue
        now = float(np.mean(list(ps.values())))
        emit("rebar", "steel_vn", f"Thép thanh CB300 D10 – TB {len(ps)} hãng", rname, "VND/kg", now, items[next(iter(ps))].get("as_of"), vs,
             "Pass-through: %Δ = 0,45×%Δ(chỉ số đầu vào: 45% quặng + 35% phế + 20% HRC) + 0,6×%Δ USD/VND", "steelonline.vn (giá niêm yết) + mô hình đầu vào",
             "Thấp–Trung bình", pair="rebar", extra={"brands": {i.split("_mien")[0].replace("vnsteel_", "").replace("_", " ").title(): p for i, p in ps.items()},
                                                      "region_label": lbl})
    # ---- cement / sand / stone / concrete (cost models) ----
    def cement_pct():
        return {h: blend({"coal": 0.30, "brent": 0.08}, h, INFL, 0.05) for h in H}
    def sand_pct():   # cát/đá: vận chuyển (diesel) + khan hiếm; nền tăng theo lạm phát
        return {h: blend({"brent": 0.15}, h, INFL + 0.01, 0.07) for h in H}
    cp, sp = cement_pct(), sand_pct()
    def concrete_pct():  # tỷ trọng chi phí 1 m³ bê tông M250-300: xi măng 32%, cát 10%, đá 18%, nhiên liệu/vận chuyển 8%, khác 32%
        r = {}
        for h in H:
            b = 0.32 * cp[h][0] + 0.28 * sp[h][0] + 0.08 * pct("brent", h) + 0.32 * INFL * h / 12
            sd = math.sqrt((0.32 * cp[h][1]) ** 2 + (0.28 * sp[h][1]) ** 2 + (0.08 * W["brent"]["fc"][h]["sd"]) ** 2 + (0.03 * math.sqrt(h / 12)) ** 2)
            r[h] = (b, sd)
        return r
    ccp = concrete_pct()
    def g(i): return items.get(i, {}).get("price")
    local = [
      ("cement", "cement", "Xi măng PCB40 bao", [("HN", g("hn_sxd_q3_08"), "Sở XD Hà Nội Q3/2026 – Vicem Bút Sơn PCB40 bao (tại NM)"), ("HCM", g("vnmat_xi_mang_xi_mang_pcb40_bao"), "thitruonghanghoa.com (công bố giá Sở XD TP.HCM)")], "VND/tấn", cp,
       "Chi phí: 30% than + 8% dầu + 62% khác (lạm phát 3,5%/năm, giả định) + sai số riêng 5%/năm"),
      ("sand", "sand_stone", "Cát vàng / cát bê tông", [("HN", g("hn_sxd_q3_01"), "Sở XD Hà Nội Q3/2026 – cát vàng bãi Trung Hà"), ("HCM", g("vnmat_cat_cat_be_tong_gia_binh_quan_khu_vuc"), "thitruonghanghoa.com – cát bê tông BQ khu vực")], "VND/m³", sp,
       "Xu hướng: lạm phát+1%/năm, 15% theo dầu (vận chuyển), sai số riêng 7%/năm"),
      ("stone", "sand_stone", "Đá 1x2", [("HN", (g("hn_sxd_q3_04") + g("hn_sxd_q3_05")) / 2 if g("hn_sxd_q3_04") and g("hn_sxd_q3_05") else None, "Sở XD Hà Nội Q3/2026 – TB 2 điểm KD"), ("HCM", g("vnmat_da_xay_dung_da_1x2_gia_binh_quan_khu_vuc"), "thitruonghanghoa.com – BQ khu vực")], "VND/m³", sp,
       "Như cát"),
    ]
    # bê tông: lấy nguồn bổ sung (DB nếu đã tích hợp vào fetcher, nếu không gọi trực tiếp)
    rmc = {i: m for i, m in items.items() if i.startswith("rmc_")}
    if not rmc:
        try: rmc = {r["id"]: r for r in S.src_concrete()}
        except Exception as e: notes.append(f"Bê tông: lỗi nguồn {e}")
    for gr in ("250", "300", "400"):
        novat = lambda m: "gồm VAT" not in (m.get("note") or "")  # compare like with like: ex-VAT price lists only
        hn = [m["price"] for i, m in rmc.items() if i.startswith("rmc_hn") and i.endswith(gr) and novat(m)]
        hc = [m["price"] for i, m in rmc.items() if i.startswith("rmc_hcm") and i.endswith(gr) and novat(m)]
        hcs = ", ".join(sorted({{"dvc": "betongdvc.com", "dn": "betongdongnam.com"}.get(i.split("_")[2], i.split("_")[2]) for i, m in rmc.items() if i.startswith("rmc_hcm") and i.endswith(gr) and novat(m)}))
        local.append((f"rmc{gr}", "concrete", f"Bê tông tươi M{gr} đá 1x2", [("HN", float(np.mean(hn)) if hn else None, f"TB {len(hn)} NCC Hà Nội (betonghanoi.com.vn, betongtuoichem.com), cát thường"),
                      ("HCM", float(np.mean(hc)) if hc else None, f"TB {len(hc)} NCC TP.HCM ({hcs}), giá chưa VAT")], "VND/m³", ccp,
                      "Chi phí cấu thành: 32% xi măng + 10% cát + 18% đá + 8% nhiên liệu + 32% khác (lạm phát)"))
    for key, grp, nm, regs, unit, fp, meth in local:
        for reg, v, s_ in regs:
            if not v: continue
            emit(key, grp, nm, reg, unit, float(v), "Q3/2026" if "Sở XD Hà Nội" in s_ else NOW.date().isoformat(), fp, meth, s_, "Thấp", pair=key)
    # ---- plastics ----
    pl = {}
    for slug, (iid, nm) in S.TE_PLASTIC.items():
        try: x = S.parse_te_desc(S.te_desc(slug))
        except Exception: x = None
        if x: pl[iid] = (nm, x, slug)
    ppct = {h: (0.45 * pct("brent", h), math.sqrt((0.45 * W["brent"]["fc"][h]["sd"]) ** 2 + (0.12 * math.sqrt(h / 12)) ** 2)) for h in H}
    for iid, (nm, x, slug) in pl.items():
        emit("pe" if "ethylene" in nm else ("pvc" if "PVC" in nm else "pp"), "plastics", nm, None, "CNY/tấn", x["price"], x["as_of"], ppct,
             "Hồi quy theo dầu: %Δ = 0,45×%Δ Brent (dự báo Brent có futures) + sai số riêng 12%/năm; không có chuỗi lịch sử miễn phí để backtest",
             f"Trading Economics ({slug})", "Thấp", trend={"mom": x["ch1m"], "yoy": x["ch1y"], "src": "TE"})
    try:
        for r in S.src_hdpe_pipe():
            if r["id"].endswith("d110_pn10"):
                hp = {h: (0.55 * ppct[h][0] + 0.45 * INFL * h / 12, math.sqrt((0.55 * ppct[h][1]) ** 2 + (0.03) ** 2)) for h in H}
                emit("hdpe_pipe", "plastics", r["name"], "HCM", "VND/m", r["price"], NOW.date().isoformat(), hp,
                     "55% nguyên liệu PE (theo dầu) + 45% chi phí khác (lạm phát); giá bảng – nhà SX điều chỉnh theo đợt", r["src"], "Thấp")
    except Exception as e: notes.append(f"HDPE pipe: {e}")
    # ---- MEP: VND metal & equipment cost-driver indices ----
    fxp = {h: pct("usdvnd", h) for h in H}
    for k, key, nm in [("copper", "cu_vnd", "Đồng quy VND (đầu vào cáp điện)"), ("alu", "al_vnd", "Nhôm quy VND (cáp nhôm, thanh cái, vỏ ĐH)")]:
        now = W[k]["y"].iloc[-1] * W["usdvnd"]["y"].iloc[-1] / 1000
        emit(key, "copper" if k == "copper" else "aluminium", nm, None, "VND/kg", now, NOW.date().isoformat(),
             {h: (pct(k, h) + fxp[h], wfc(k)[h][1]) for h in H}, "Giá LME dự báo × USD/VND dự báo", "LME (Westmetall) × Vietcombank/Yahoo", "Trung bình")
    IDX = [("idx_cable", "Cáp điện hạ thế (CV/CXV)", {"copper": 0.65, "brent": 0.05}, "Đồng ~60–70% giá cáp; PVC/XLPE theo dầu"),
           ("idx_transformer", "Máy biến áp", {"copper": 0.25, "hrc": 0.20, "alu": 0.05, "brent": 0.05}, "Dây quấn đồng/nhôm, tôn silic (proxy HRC), dầu MBA"),
           ("idx_elevator", "Thang máy", {"hrc": 0.25, "copper": 0.05}, "Thép kết cấu/cabin, động cơ; phần lớn là thiết bị/lắp đặt"),
           ("idx_hvac", "Điều hòa / Chiller (HVAC)", {"copper": 0.15, "alu": 0.10, "hrc": 0.15}, "Ống đồng, lá tản nhiệt nhôm, vỏ thép"),
           ("idx_switchboard", "Tủ điện / thang máng cáp / rack", {"hrc": 0.30, "copper": 0.20}, "Vỏ thép tấm, thanh cái đồng"),
           ("idx_genset", "Máy phát điện", {"hrc": 0.15, "copper": 0.10}, "Khung thép, máy phát (dây quấn đồng)")]
    for key, nm, w, why in IDX:
        fp = {h: (blend(w, h, INFL)[0] + (1 - 0) * 0.6 * fxp[h], blend(w, h, INFL, 0.03)[1]) for h in H}
        meth = "Chỉ số chi phí đầu vào = " + " + ".join(f"{int(v*100)}% {NM[k][0].split(' (')[0]}" for k, v in w.items()) + f" + {int(round((1-sum(w.values()))*100))}% khác (lạm phát 3,5%) ; +0,6×%Δ USD/VND (thiết bị nhập khẩu)"
        emit(key, "mep_index", nm, None, "chỉ số (nay=100)", 100.0, NOW.date().isoformat(), fp, meth, "Tổng hợp từ dự báo đầu vào", "Thấp",
             extra={"why": why, "is_index": True})
    # ---- scenarios ----
    def scen_adj(group, h, side):
        tot, parts = 0.0, []
        for d in drivers["drivers"]:
            imp = d.get("impact_" + side) or (d.get("impact") if d["dir"] == side else None)
            if not imp: continue
            v = imp.get(group)
            if v: tot += v * math.sqrt(h / 12); parts.append([d["id"], round(v * math.sqrt(h / 12), 2)])
        return tot / 100, parts
    GROUPMAP = {"mep_index": None}
    for it in out_items:
        if not it.get("fc"): continue
        grp = it["group"]
        for h in H:
            f = it["fc"][str(h)]
            if grp == "mep_index":  # suy ra từ nhóm đầu vào của chỉ số
                w = next(x[2] for x in IDX if x[0] == it["key"])
                gm = {"copper": "copper", "alu": "aluminium", "hrc": "steel_world", "brent": "energy"}
                up = sum(v * scen_adj(gm[k], h, "up")[0] for k, v in w.items()); dn = sum(v * scen_adj(gm[k], h, "down")[0] for k, v in w.items())
                pu, pd_ = [], []
            else:
                up, pu = scen_adj(grp, h, "up"); dn, pd_ = scen_adj(grp, h, "down")
                if grp == "ironore": pass
            f["bull"] = f["base"] * (1 + up); f["bear"] = f["base"] * (1 + dn); f["bull_parts"] = pu; f["bear_parts"] = pd_
    # ---- pair insights HN vs HCM ----
    INS = {"rebar": "Giá niêm yết miền Nam thường cao hơn do chi phí vận chuyển từ các lò lớn phía Bắc/miền Trung (Hòa Phát Hải Dương, Dung Quất) và cạnh tranh thấp hơn ở phân khúc cuộn.",
           "cement": "Lưu ý khác điều kiện giao: HN là giá tại máng xuất nhà máy (Sở XD HN), HCM là giá bán BQ khu vực – chênh lệch phần lớn do cước vận chuyển clinker/xi măng từ miền Bắc vào Nam.",
           "sand": "Cát miền Nam phụ thuộc nguồn ĐBSCL/Campuchia; HN dùng cát sông Lô/sông Hồng – cả hai đều chịu siết khai thác, HN biến động mạnh ở cát đen.",
           "stone": "HCM phải vận chuyển đá từ Bình Dương/Đồng Nai/Vũng Tàu xa hơn; HN có mỏ gần (Hòa Bình, Hà Nam) nên giá thấp hơn.",
           "rmc250": "Bê tông HCM đắt hơn chủ yếu do giá cát, đá và xi măng tại chỗ cao hơn; NCC HN chênh nhau lớn (cát thường/cát vàng, mức chiết khấu).",
           "rmc300": "Như M250 – chênh lệch cấp phối M300 so với M250 ~40–100k đ/m³ ở cả hai miền.",
           "rmc400": "Mác cao dùng cho cột/vách cao tầng: nhiều xi măng hơn nên nhạy với giá xi măng; khoảng giá HN rộng (cát thường vs cát vàng, chênh NCC), nên so sánh vùng phụ thuộc mốc giá chọn."}
    pairs = {}
    for it in out_items:
        if it.get("pair") and it.get("region"): pairs.setdefault(it["pair"], {})[it["region"]] = it
    pair_out = []
    for k, d in pairs.items():
        if "HN" in d and "HCM" in d:
            diff = 100 * (d["HCM"]["now"] / d["HN"]["now"] - 1)
            pair_out.append({"key": k, "name": d["HN"]["name"], "hn": d["HN"]["id"], "hcm": d["HCM"]["id"], "diff_pct": round(diff, 1),
                             "insight": f"TP.HCM {'cao' if diff > 0 else 'thấp'} hơn Hà Nội {abs(diff):.1f}%. " + INS.get(k, "")})
    # ---- latest TE commentary (auto, refreshed each run) ----
    te_comments = {}
    for slug in ["steel", "copper", "aluminum", "brent-crude-oil", "coal", "iron-ore"]:
        try:
            t = requests.get(f"https://tradingeconomics.com/commodity/{slug}", headers=S.UA, timeout=30).text
            m = re.search(r'id="description"[^>]*>(.*?)</div>', t, re.S)
            if m:
                import html as _h
                txt = re.sub(r"\s+", " ", _h.unescape(re.sub("<[^>]+>", " ", m.group(1)))).strip()
                if len(txt) > 200 and "according to trading on a contract" not in txt[:200]:
                    te_comments[slug] = {"text": txt[:900], "url": f"https://tradingeconomics.com/commodity/{slug}"}
        except Exception: pass
    out = {"generated": NOW.isoformat(timespec="minutes"), "horizons": H, "items": out_items, "pairs": pair_out, "drivers": drivers,
           "te_comments": te_comments, "curves": curves, "notes": notes, "assumptions": {"infl": INFL, "steel_beta": 0.45, "fx_beta_steel": 0.6},
           "sources": src}
    os.makedirs(a.site, exist_ok=True)
    json.dump(out, open(os.path.join(a.site, "forecast.json"), "w"), ensure_ascii=False, default=lambda o: float(o) if isinstance(o, (np.floating,)) else str(o))
    shutil.copy(os.path.join(HERE, "forecast.html"), os.path.join(a.site, "forecast.html"))
    print("forecast ->", a.site, len(out_items), "items;", "notes:", notes)

if __name__ == "__main__":
    main()
