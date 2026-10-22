import sqlite3, json, io, csv, os, datetime as dt
from zoneinfo import ZoneInfo
from flask import Flask, jsonify, send_from_directory, Response, request, abort

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "data", "prices.db")
TZ = ZoneInfo("Asia/Saigon")
OZ_PER_LUONG = 37.5 / 31.1034768
LB_PER_T = 2204.62262
SHORT_TON_PER_T = 1.10231131
STALE_HOURS = 30  # a successfully fetched item not refreshed in this long is shown as stale
app = Flask(__name__, static_folder=None)

def db():
    import store; store.ensure_db(DB)
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c

def build_rows():
    c = db()
    items = c.execute("select * from items").fetchall()
    meta = {r["id"]: json.loads(r["meta"]) for r in items}
    fx = {k: meta.get(f"fx_{k}_vnd", {}).get("price") for k in ("usd", "cny", "eur")}
    now = dt.datetime.now(TZ)
    rows = []
    for r in items:
        m = meta[r["id"]]
        if m.get("hidden"): continue
        # previous distinct observation (different source date or price) for change %
        hist = c.execute("select as_of, price from obs where id=? order by fetched_at desc limit 60", (r["id"],)).fetchall()
        prev = m.get("prev")
        if prev is None:
            for h in hist[1:]:
                if h["as_of"] != m.get("as_of"):
                    prev = h["price"]; break
        chg = m.get("change_pct")
        if chg is None and prev:
            chg = (m["price"] / prev - 1) * 100
        # VND conversion
        vnd, vnd_unit = None, None
        rate = fx.get(m["currency"].lower()) if m["currency"] != "VND" else None
        if rate:
            u = m["unit"].split("/", 1)[1]
            if u == "lb": vnd, vnd_unit = m["price"] * LB_PER_T * rate, "VND/tấn"
            elif u == "short ton": vnd, vnd_unit = m["price"] * SHORT_TON_PER_T * rate, "VND/tấn"
            elif u == "oz": vnd, vnd_unit = m["price"] * OZ_PER_LUONG * rate, "VND/lượng"
            else: vnd, vnd_unit = m["price"] * rate, "VND/" + u
        last_ok = dt.datetime.fromisoformat(r["last_ok"])
        stale = r["status"] != "ok" or (now - last_ok).total_seconds() > STALE_HOURS * 3600
        rows.append(dict(m, status=r["status"], stale=stale, last_ok=r["last_ok"], last_try=r["last_try"],
                         change_pct=chg, prev=prev, vnd=vnd, vnd_unit=vnd_unit,
                         group=m.get("grp") or m.get("group")))
    order = {"world": 0, "vn": 1}
    rows.sort(key=lambda x: (order.get(x["group"], 9), x["category"], x.get("region") or "", x["name"]))
    return rows

@app.get("/")
def index(): return send_from_directory(os.path.join(BASE, "static"), "index.html")

@app.get("/static/<path:p>")
def static_files(p): return send_from_directory(os.path.join(BASE, "static"), p)

@app.get("/api/prices")
def prices():
    rows = build_rows()
    c = db()
    runs = [dict(r) for r in c.execute(
        "select source, fetched_at, ok, n, error from runs where fetched_at=(select max(fetched_at) from runs)")]
    last = c.execute("select max(fetched_at) from runs").fetchone()[0]
    fx = next((r for r in rows if r["id"] == "fx_usd_vnd"), None)
    return jsonify(updated_at=last, usd_vnd=fx and fx["price"], items=rows, sources=runs,
                   tunnel_url=open(os.path.join(BASE, "data", "tunnel_url.txt")).read().strip()
                   if os.path.exists(os.path.join(BASE, "data", "tunnel_url.txt")) else None)

@app.get("/api/history/<iid>")
def history(iid):
    c = db()
    if not c.execute("select 1 from items where id=?", (iid,)).fetchone(): abort(404)
    rows = c.execute("select fetched_at, as_of, price, price_high from obs where id=? order by fetched_at", (iid,)).fetchall()
    # one point per source date (last fetch of that day)
    byday = {}
    for r in rows: byday[r["as_of"] or r["fetched_at"][:10]] = dict(r)
    # compact: charts only need date + price (price_high only for range-priced items)
    pts = []
    for k, v in sorted(byday.items()):
        p = {"date": k, "price": round(v["price"], 6) if v["price"] is not None else None}
        if v["price_high"] is not None: p["price_high"] = round(v["price_high"], 6)
        pts.append(p)
    return Response(json.dumps(dict(id=iid, points=pts), ensure_ascii=False, separators=(",", ":")), mimetype="application/json")

@app.get("/api/history.csv")
def history_csv():
    """Full price history (all items, 1 row/item/day) for download."""
    c = db(); meta = {r["id"]: json.loads(r["meta"]) for r in c.execute("select id, meta from items")}
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow(["Ngày giá", "Mã", "Mặt hàng", "Danh mục", "Khu vực", "Giá", "Giá cao (khoảng)", "Đơn vị", "Tiền tệ", "Nguồn"])
    rows = c.execute("""select id, coalesce(as_of, substr(fetched_at,1,10)) d, price, price_high from (
        select o.*, row_number() over (partition by id, coalesce(as_of, substr(fetched_at,1,10)) order by fetched_at desc) rn
        from obs o) where rn=1 order by d, id""")
    for r in rows:
        m = meta.get(r["id"], {})
        if m.get("hidden"): continue
        w.writerow([r["d"], r["id"], m.get("name", ""), m.get("category", ""), m.get("region") or "", r["price"],
                    "" if r["price_high"] is None else r["price_high"], m.get("unit", ""), m.get("currency", ""),
                    (m.get("src") or "").split(" [")[0]])
    return Response("\ufeff" + buf.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=lich-su-gia-vat-lieu.csv"})

@app.get("/api/sources")
def sources():
    c = db()
    return jsonify([dict(r) for r in c.execute("select * from runs order by fetched_at desc limit 200")])

COLS = [("group", "Nhóm"), ("category", "Danh mục"), ("name", "Mặt hàng"), ("region", "Khu vực"), ("price", "Giá"),
        ("price_high", "Giá cao (khoảng)"), ("unit", "Đơn vị"), ("currency", "Tiền tệ"), ("vnd", "Quy đổi VND"),
        ("vnd_unit", "Đơn vị VND"), ("change_pct", "Thay đổi %"), ("as_of", "Ngày giá"), ("last_ok", "Cập nhật lúc"),
        ("stale", "Dữ liệu cũ"), ("src", "Nguồn"), ("url", "Link nguồn"), ("note", "Ghi chú")]

import unicodedata
def _norm(t): return unicodedata.normalize("NFD", t.lower().replace("đ", "d")).encode("ascii", "ignore").decode()
GROUP_VN = {"world": "Thế giới", "vn": "Việt Nam"}
def filtered():
    rows = build_rows(); q = _norm(request.args.get("q") or ""); g = request.args.get("group")
    if g: rows = [r for r in rows if r["group"] == g]
    if q:
        rows = [r for r in rows if all(w in _norm(" ".join(str(r.get(k) or "") for k in ("name", "category", "region", "src", "brand")))
                                       for w in q.split())]
    return [dict(r, group=GROUP_VN.get(r["group"], r["group"]), stale="Có" if r["stale"] else "") for r in rows]

@app.get("/api/export.csv")
def export_csv():
    buf = io.StringIO(); w = csv.writer(buf)
    w.writerow([h for _, h in COLS])
    for r in filtered(): w.writerow([r.get(k) if r.get(k) is not None else "" for k, _ in COLS])
    fn = f"bang-gia-vat-lieu-{dt.datetime.now(TZ):%Y%m%d-%H%M}.csv"
    return Response("\ufeff" + buf.getvalue(), mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f"attachment; filename={fn}"})

@app.get("/api/export.xlsx")
def export_xlsx():
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook(); ws = wb.active; ws.title = "Bang gia"
    ws.append([h for _, h in COLS]); [setattr(c, "font", Font(bold=True)) for c in ws[1]]
    for r in filtered(): ws.append([r.get(k) for k, _ in COLS])
    for col, w in zip("ABCDEFGHIJKLMNOPQ", [8, 18, 45, 14, 14, 14, 14, 8, 18, 12, 10, 12, 22, 8, 30, 40, 40]):
        ws.column_dimensions[col].width = w
    bio = io.BytesIO(); wb.save(bio)
    fn = f"bang-gia-vat-lieu-{dt.datetime.now(TZ):%Y%m%d-%H%M}.xlsx"
    return Response(bio.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename={fn}"})

@app.get("/healthz")
def health(): return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
