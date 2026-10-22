#!/usr/bin/env python3
"""Lượt xem theo ngày (giờ Việt Nam) -> data/views/daily.csv (git) + site/views-daily.json.
Nguồn chính: GoatCounter API /api/v0/stats/total (token GOATCOUNTER_TOKEN, chỉ đọc; múi giờ tài khoản = Asia/Ho_Chi_Minh).
Dự phòng không token: public counter (start=D&end=D+1, end exclusive). 1–3 request/lần chạy; không gọi theo từng lượt xem.
Lỗi mạng => giữ số cũ trong CSV."""
import csv, json, os, sys, datetime as dt, urllib.request
from zoneinfo import ZoneInfo
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "data", "views", "daily.csv"); OUT = os.path.join(ROOT, "site", "views-daily.json")
GC = "https://cscm-vn.goatcounter.com"; FIRST = dt.date(2026, 10, 22); N = 30; VN = ZoneInfo("Asia/Ho_Chi_Minh")
def token():
    t = os.environ.get("GOATCOUNTER_TOKEN", "").strip()
    p = "/workspace/.secrets/goatcounter_api.txt"
    if not t and os.path.exists(p): t = open(p).read().strip()
    return t
def get(url, tok=None):
    h = {"User-Agent": "cscm-vn-views"}
    if tok: h["Authorization"] = "Bearer " + tok
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=30) as r: return json.load(r)
def main():
    have = {}
    if os.path.exists(CSV):
        with open(CSV, newline="") as f: have = {r["date"]: int(r["views"]) for r in csv.DictReader(f)}
    today = dt.datetime.now(VN).date(); d0 = today - dt.timedelta(days=N - 1); src = "cache"
    tok = token()
    try:
        if not tok: raise RuntimeError("no token")
        j = get(f"{GC}/api/v0/stats/total?start={max(FIRST, d0)}&end={today + dt.timedelta(days=1)}", tok)
        for s in j["stats"]:
            if FIRST <= dt.date.fromisoformat(s["day"]) <= today: have[s["day"]] = int(s["daily"])
        src = "api"
    except Exception as e:
        print("views api:", type(e).__name__, str(e)[:120], "-> public counter", file=sys.stderr)
        d = max(FIRST, today - dt.timedelta(days=2))
        while d <= today:
            try: have[str(d)] = int(get(f"{GC}/counter/TOTAL.json?start={d}&end={d + dt.timedelta(days=1)}")["count"]); src = "public"
            except Exception as e2: print("views public", d, e2, file=sys.stderr)
            d += dt.timedelta(days=1)
    os.makedirs(os.path.dirname(CSV), exist_ok=True)
    with open(CSV, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["date", "views"]); [w.writerow([k, have[k]]) for k in sorted(have)]
    days = [{"d": str(d0 + dt.timedelta(days=i)), "n": have.get(str(d0 + dt.timedelta(days=i)))} for i in range(N)]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"updated": dt.datetime.now(VN).isoformat(timespec="minutes"), "tz": "Asia/Ho_Chi_Minh", "source": src,
               "since": str(FIRST), "total": sum(have.values()), "days": days}, open(OUT, "w"), separators=(",", ":"))
    print(f"views: source={src} today={have.get(str(today))} total={sum(have.values())}")
if __name__ == "__main__": main()
