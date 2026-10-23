#!/usr/bin/env python3
"""Điểm nóng theo nhóm danh mục cấp 1 (ô "Danh mục mua sắm" trang chủ) -> trends/data/highlights.json (+ site/data/).
Chạy trong CI sau feeds.py / legal_feed.py, trước build.py (build.py chép trends/data/*.json sang site/data/).
Chỉ dùng dữ liệu thật: lịch sử giá data/history/prices/*.csv (append-only), trends/data/feed.json, market.json, legal-feed.json.

Ngưỡng biến động ngày (Δd = giá phiên mới nhất so với phiên liền trước của CHÍNH mã đó):
  - Hàng hóa thế giới biến động mạnh (LME/SHFE/TE/Yahoo: kim loại, quặng, than, nhựa)  |Δd| >= 2,0%
  - Vàng / bạc                                                                         |Δd| >= 2,0%
  - Tỷ giá (fx_*)                                                                      |Δd| >= 0,5%
  - Vật liệu xây dựng trong nước (thép, xi măng, bê tông, gạch, cát đá, ống, cáp…)      |Δd| >= 1,0%
  Phiên mới nhất phải trong 4 ngày gần đây (cuối tuần LME nghỉ) và phiên trước cách <= 10 ngày;
  các nguồn trùng một hàng hóa (lme_/te_/yf_copper…) chỉ giữ 1 dòng lớn nhất.
Tin mới: tin trong feed/market/legal có ngày >= hôm qua (giờ VN) và điểm >= NEWS_MIN, gắn nhóm qua 'tax' (taxonomy cấp 2 -> cấp 1);
  legal-feed mục 'trade' (phòng vệ thương mại/thuế quan) -> nhóm Vĩ mô & thương mại.
Xếp hạng trong nhóm: biến động giá (theo |Δd|/ngưỡng) trước, sau đó tin (điểm score)."""
import csv, glob, json, os, re, sys, datetime as dt
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); sys.path.insert(0, H)
from build import classify, TAX, J, strip  # same taxonomy mapping as hub.json
TZ = dt.timezone(dt.timedelta(hours=7))
NEWS_MIN = 3.5  # điểm "nóng" tối thiểu của tin RSS (feeds.py chấm 0–10); tin market.json (biên tập) luôn tính
# Tin chỉ tính cho ô nhóm khi tiêu đề (không dấu) chứa từ khóa vật tư/NCC/quy định của CHÍNH nhóm đó; tin BĐS chung bị loại.
# Nhóm 'tt' (Vĩ mô) giữ tin vĩ mô/thương mại/nhà thầu nhưng tin có từ khóa vật tư được xếp trước.
KW = dict(
 xd=r"thep|phoi thep|quang sat|than coc|xi mang|clinker|be tong|cat xay|cat san|da xay|da 1x2|vat lieu xay dung|vlxd|gach (xay|nung|khong nung|aac)|cop pha|van khuon|chong tham|steel|rebar|hrc|iron ore|cement|concrete|sand|aggregate|hoa phat|hoa sen|vicem|formosa",
 mep=r"gia dong|dong lme|dong do|quang dong|cap dong|nhom|cap dien|day dien|dieu hoa|hvac|chiller|thang may|may phat|ong nuoc|ong nhua|pvc|hdpe|ppr|tu dien|bien ap|pccc|chua chay|dien mat troi|copper|alumin|cable|elevator|transformer|cadivi|daikin|schneider",
 ht=r"gach (op|lat|men|granite|porcelain)|ceramic|thiet bi ve sinh|tbvs|\\bson (nuoc|dau|tuong|chong|phu|epoxy|noi that|ngoai that)|\\bpaint|go cong nghiep|san go|san go|vach thach cao|thach cao|gypsum|da op|da granite|da marble|tu bep|bep tu|viglacera|inax|toto|dong tam|prime|thach ban|jotun|dulux|kova",
 md=r"kinh|nhom dinh hinh|nhom kinh|cua nhom|mat dung|facade|glass|curtain wall|alu|xingfa|austdoor|eurowindow",
 elv=r"smart home|nha thong minh|camera|an ninh|bms|elv|iot|khoa dien tu|bkav|lumi|hikvision",
 cq=r"canh quan|cay xanh|cay trong|vuon uom|co nhan tao|da canh quan|da tu nhien|ho boi|tieu canh|landscape|cong vien",
 esg=r"xanh|carbon|cbam|leed|edge|lotus|phat thai|net zero|tai che|nang luong tai tao|esg",
 tt=r"\\b(thep|xi mang|vat lieu|vlxd|thue|chong ban pha gia|phong ve thuong mai|ty gia|xang dau|nha thau|tong thau|coteccons|hoa binh|ricons|xuat khau|nhap khau|lai suat|lam phat|cpi|fdi)\\b|gia (vat lieu|thep|xang|dien|nhien lieu)")
EXCL = r"can ho|khu do thi|huy dong von|chung cu|biet thu|bat dong san|bds|nha o|du an .*(mo ban|ra mat)|gia dat|condotel|tham quan nha mau|luat dat dai"
TH = dict(world=2.0, gold=2.0, fx=0.5, vn=1.0)
LAB = dict(world="hàng hóa thế giới", gold="kim loại quý", fx="tỷ giá", vn="vật liệu trong nước")
def kind(iid, meta):
    if iid.startswith("fx_"): return "fx"
    if re.search(r"gold|silver|sjc", iid): return "gold"
    return "world" if meta.get("grp") == "world" else "vn"
def short(name, n=42):
    name = re.sub(r"\s*[–-]\s*(giá|gia) .*$", "", name or "").strip(); return name if len(name) <= n else name[:n - 1].rstrip() + "…"
def main(today=None):
    today = today or dt.datetime.now(TZ).date()
    reg = {x["id"]: x.get("meta", {}) for x in J(os.path.join(ROOT, "data/registry/items.json"), [])}
    parent = {c["id"]: n["id"] for n in TAX["tree"] for c in n["children"]}
    files = sorted(glob.glob(os.path.join(ROOT, "data/history/prices/*.csv")))[-2:]
    last = {}  # id -> {date: price (last row of that date)}
    for f in files:
        for r in csv.DictReader(open(f, encoding="utf-8")):
            try: p = float(r["price"]); h = float(r["price_high"]) if r.get("price_high") else None
            except ValueError: continue
            last.setdefault(r["item_id"], {})[r["date"]] = (p + h) / 2 if h else p
    G = {n["id"]: dict(id=n["id"], name=n["name"], icon=n["icon"], prices=[], news=[], n_news=0) for n in TAX["tree"]}
    best = {}
    for iid, ser in last.items():
        meta = reg.get(iid)
        if not meta: continue
        ds = sorted(ser)
        if len(ds) < 2: continue
        d1, d0 = dt.date.fromisoformat(ds[-1]), dt.date.fromisoformat(ds[-2])
        if (today - d1).days > 4 or (d1 - d0).days > 10 or not ser[ds[-2]]: continue
        ch = round((ser[ds[-1]] / ser[ds[-2]] - 1) * 100, 2); k = kind(iid, meta)
        if abs(ch) < TH[k]: continue
        tax = classify(dict(meta, id=iid)); g = parent.get(tax, "tt")
        if k == "fx": g = "tt"
        key = (g, re.sub(r"^(lme|te|yf)_", "", iid)) if k != "vn" else (g, iid)
        row = dict(id=iid, name=short(meta.get("name") or iid), region=meta.get("region") or "", d1=ch, date=ds[-1], prev_date=ds[-2],
                   price=ser[ds[-1]], unit=meta.get("unit"), kind=k, threshold=TH[k], tax=tax, url=f"mat-hang.html?id={iid}", w=abs(ch) / TH[k])
        if key not in best or row["w"] > best[key]["w"]: best[key] = row
    for (g, _), row in best.items(): G[g]["prices"].append(row)
    since = (today - dt.timedelta(days=1)).isoformat(); seen = set()
    def add_news(g, x, title, url, date, score, src):
        if g not in G or (score or 0) < NEWS_MIN or not title or title.lower() in seen: return
        t = strip(title); m = re.search(KW[g], t)
        if g != "tt" and (not m or re.search(EXCL, t)): return
        mat = re.search("|".join(v for k, v in KW.items() if k not in ("tt", "esg")), t)
        if g == "tt" and (re.search(EXCL, t) and not mat or not m and not mat): return
        score = (score or 0) + (3 if (mat and not re.search(EXCL, t)) else 0)  # tin có từ khóa vật tư xếp trước
        seen.add(title.lower()); G[g]["news"].append(dict(title=title, url=url, date=date, score=score or 0, source=src))
    for x in J(os.path.join(H, "data/market.json"), {"items": []})["items"]:  # curated market notes first
        if (x.get("date") or "") >= since:
            for t in (x.get("tax") or [])[:1]:
                add_news(parent.get(t), x, x["title"], f"thi-truong.html#{x['id']}", x["date"], 10, (x.get("sources") or [{}])[0].get("name", ""))
    for x in J(os.path.join(H, "data/feed.json"), {"items": []})["items"]:
        if (x.get("date") or "") >= since and x.get("kind") in ("market", "trend", "contractor"):
            for t in (x.get("tax") or [])[:1]: add_news(parent.get(t), x, x["title"], x["url"], x["date"], x.get("score"), x.get("source"))
    for x in J(os.path.join(H, "data/legal-feed.json"), {"items": []})["items"]:
        if (x.get("published") or "")[:10] >= since and x.get("section") == "trade":
            add_news("tt", x, x["title"], x["url"], x["published"][:10], 5, x.get("source"))
    out = []
    for g in G.values():
        g["prices"].sort(key=lambda r: -r["w"]); g["news"].sort(key=lambda r: r["date"], reverse=True); g["news"].sort(key=lambda r: -r["score"])
        g["n_news"] = len(g["news"]); g["n_moves"] = len(g["prices"]); g["prices"] = g["prices"][:3]; g["news"] = g["news"][:3]
        for r in g["prices"]: r.pop("w")
        g["rank"] = round(sum(min(abs(r["d1"]) / r["threshold"], 5) for r in g["prices"]) + min(g["n_news"], 10) * 0.3, 2)
        g["link"] = f"danh-muc.html?c={g['id']}"; out.append(g)
    top = sorted([g for g in out if g["prices"] or g["news"]], key=lambda g: -g["rank"])[:3]
    res = dict(schema_version=1, built=dt.datetime.now(TZ).isoformat(timespec="minutes"), today=today.isoformat(), news_since=since,
               thresholds={k: dict(abs_pct=v, label=LAB[k]) for k, v in TH.items()}, top=[g["id"] for g in top], groups=out)
    for p in (os.path.join(H, "data/highlights.json"), os.path.join(ROOT, "site/data/highlights.json")):
        if os.path.isdir(os.path.dirname(p)): json.dump(res, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for g in out: print(g["id"], "moves", g["n_moves"], [(r["name"], r["region"], r["d1"]) for r in g["prices"]], "news", g["n_news"])
if __name__ == "__main__": main()
