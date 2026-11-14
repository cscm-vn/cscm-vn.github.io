#!/usr/bin/env python3
"""Dải "Mới hôm nay" + nhãn MỚI -> trends/data/fresh.json (build.py chép sang site/data/).
Chạy trong CI sau export_static.py / feeds.py / policy_feed.py, TRƯỚC trends/build.py.

- Tin (trends.json, market.json, feed.json RSS, policy-feed.json): mỗi mục có `ts` = lần đầu site thấy mục đó
  (trạng thái lưu ở trends/data/fresh_seen.json, CI commit lại; policy-feed dùng sẵn `found`).
  Chỉ tính tin có ngày đăng/ngày thêm trong 2 ngày gần đây (giờ VN) để bài cũ mới quét được không bị gắn MỚI.
- Giá (data/history/prices/*.csv, append-only, 1 dòng/mã/ngày): lần đổi giá gần nhất của mỗi mã =
  dòng mới nhất có giá khác dòng liền trước; `ts` = fetched_at của dòng đó.
Tệp xuất chứa mọi mục có ts trong WINDOW_H giờ; trình duyệt tự lọc lại theo giờ hiện tại, nên nhãn tự mất sau 24 giờ
dù site chưa build lại."""
import csv, glob, json, os, re, datetime as dt
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); D = os.path.join(H, "data")
TZ = dt.timezone(dt.timedelta(hours=7))
WINDOW_H = 30          # xuất dư vài giờ so với 24h: client lọc chính xác theo giờ xem
KEEP_DAYS = 90         # giữ trạng thái "đã thấy" để tin không bị coi là mới khi feed cuộn lại
SEEN = os.path.join(D, "fresh_seen.json")
def J(p, default=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return default
def norm_url(u):
    u = re.sub(r"^https?://(www\.)?", "", (u or "").strip(), flags=re.I).split("#")[0]
    return u.rstrip("/")
def iso(t): return t.astimezone(TZ).isoformat(timespec="seconds")
def parse(s):
    try:
        t = dt.datetime.fromisoformat(str(s))
        return t if t.tzinfo else t.replace(tzinfo=TZ)
    except Exception: return None
def noon(d):  # ước lượng giờ cho mục chưa từng thấy lúc khởi tạo trạng thái
    try: return dt.datetime.fromisoformat(str(d)[:10] + "T12:00:00").replace(tzinfo=TZ)
    except Exception: return None

def news(now, seen, boot):
    today = now.date(); cut = (today - dt.timedelta(days=1)).isoformat()  # hôm nay hoặc hôm qua (giờ VN)
    out = []
    def add(key, ts_default, recent, **x):
        if key not in seen:  # lần đầu thấy: ghi giờ build (lúc khởi tạo: ước lượng theo ngày của mục, đánh dấu "~" = giờ ước tính)
            seen[key] = iso(min(ts_default or now, now)) + "~" if boot else iso(now)
        ts = parse(seen[key].rstrip("~"))
        if recent and ts and (now - ts).total_seconds() <= WINDOW_H * 3600: out.append(dict(x, ts=iso(ts), **({"est": 1} if seen[key].endswith("~") else {})))
    for kind, f in (("trend", "trends.json"), ("market", "market.json")):
        for it in (J(os.path.join(D, f), {}) or {}).get("items", []):
            d = max(str(it.get("date") or "")[:10], str(it.get("added") or "")[:10])
            url = (it.get("sources") or [{}])[0].get("url")
            href = f"xu-huong.html?id={it['id']}" if kind == "trend" else f"thi-truong.html?id={it['id']}"
            add(f"{kind}:{it['id']}", noon(it.get("added") or it.get("date")), d >= cut, id=it["id"], kind=kind, title=it.get("title"),
                url=url, u=norm_url(url), href=href, src=(it.get("sources") or [{}])[0].get("name"), date=it.get("date"),
                org=it.get("org"), score=it.get("score"))
    for it in (J(os.path.join(D, "feed.json"), {}) or {}).get("items", []):
        if it.get("origin") == "manual": continue  # mục biên tập đã tính ở trên
        add(f"feed:{it['id']}", noon(it.get("date")), str(it.get("date") or "")[:10] >= cut, id=it["id"], kind="feed",
            title=it.get("title"), url=it.get("url"), u=norm_url(it.get("url")), href=it.get("url"), src=it.get("source"),
            date=it.get("date"), score=it.get("score"))
    for it in (J(os.path.join(D, "policy-feed.json"), {}) or {}).get("items", []):
        found = parse(it.get("found")) or noon(it.get("published"))
        pub = str(it.get("published") or it.get("found") or "")[:10]
        key = f"policy:{it['id']}"
        if key not in seen: seen[key] = iso(min(found or now, now))
        ts = parse(seen[key])
        if pub >= cut and ts and (now - ts).total_seconds() <= WINDOW_H * 3600:
            out.append(dict(id=it["id"], kind="policy", title=it.get("title"), url=it.get("url"), u=norm_url(it.get("url")),
                            href=it.get("url"), src=it.get("source"), date=pub, score=it.get("score"), ts=iso(ts)))
    return out

def prices(now):
    meta = {x["id"]: x for x in (J(os.path.join(ROOT, "site", "prices.json"), {}) or {}).get("items", [])}
    reg = {x["id"]: x.get("meta", {}) for x in J(os.path.join(ROOT, "data/registry/items.json"), []) or []}
    ser = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data/history/prices/*.csv")))[-3:]:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            try: p = float(r["price"]); h = float(r["price_high"]) if r.get("price_high") else None
            except (ValueError, TypeError): continue
            ser.setdefault(r["item_id"], {})[r["date"]] = dict(p=p, h=h, ts=r.get("fetched_at"), unit=r.get("unit"), region=r.get("region"))
    out = []
    for iid, S in ser.items():
        ds = sorted(S)
        k = next((i for i in range(len(ds) - 1, 0, -1) if (S[ds[i]]["p"], S[ds[i]]["h"]) != (S[ds[i - 1]]["p"], S[ds[i - 1]]["h"])), None)
        if k is None: continue
        cur, prev = S[ds[k]], S[ds[k - 1]]; ts = parse(cur["ts"])
        if all(str(S[d]["ts"] or "").endswith("T00:00:00+07:00") for d in ds[:k]): continue  # mã mới: mọi điểm trước là lịch sử nạp bù, không phải giá vừa đổi
        if not ts or (now - ts).total_seconds() > WINDOW_H * 3600: continue
        mid = lambda x: (x["p"] + x["h"]) / 2 if x["h"] else x["p"]
        m = meta.get(iid) or {}; g = reg.get(iid) or {}
        if m.get("stale"): continue  # nguồn lỗi đang giữ giá cũ – không gắn MỚI
        out.append(dict(id=iid, name=m.get("name") or g.get("name") or iid, region=m.get("region") or cur["region"], unit=m.get("unit") or cur["unit"],
                        grp=m.get("grp") or g.get("grp"), old=mid(prev), new=mid(cur), pct=round((mid(cur) / mid(prev) - 1) * 100, 2) if mid(prev) else None,
                        date=ds[k], prev_date=ds[k - 1], ts=iso(ts)))
    out.sort(key=lambda x: -abs(x["pct"] or 0))
    return out

def main(now=None):
    now = now or dt.datetime.now(TZ)
    st = J(SEEN); boot = st is None; seen = (st or {}).get("seen", {})
    N = news(now, seen, boot); P = prices(now)
    lim = (now - dt.timedelta(days=KEEP_DAYS)).isoformat()
    seen = {k: v for k, v in seen.items() if v >= lim}
    json.dump(dict(note="Trạng thái lần đầu thấy tin (trends/fresh.py). Không sửa tay.", seen=dict(sorted(seen.items()))),
              open(SEEN, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    kinds = {"trend": 0, "market": 1, "policy": 2, "feed": 3}
    N.sort(key=lambda x: (kinds.get(x["kind"], 9), -(x.get("score") or 0), x["ts"]))
    pr = J(os.path.join(ROOT, "site", "prices.json"), {}) or {}
    json.dump(dict(built=iso(now), prices_updated=pr.get("updated_at"), window_h=24, news=N, prices=P),
              open(os.path.join(D, "fresh.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    print(f"fresh: {len(N)} tin, {len(P)} giá đổi trong {WINDOW_H}h" + (" (khởi tạo trạng thái)" if boot else ""))
if __name__ == "__main__": main()
