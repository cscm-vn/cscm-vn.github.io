#!/usr/bin/env python3
"""Merge new trend/market items into trends/data/{trends,market}.json (keeps history, dedupes by URL/title).
Usage: python trends/merge.py new_items.json [more.json ...]
Input: a JSON list of items, or {"trends":[...], "market":[...]}. Each item needs "type": "trend"|"market"
(or is placed by the top-level key). See trends/SCHEMA.md."""
import json, sys, os, re, hashlib, unicodedata, datetime as dt
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
W = {"novelty": .15, "cost_saving": .30, "quality": .20, "applicability": .25, "supplier": .10}
TAX = {c["id"]: (n, c) for n in json.load(open((os.path.join(os.path.dirname(os.path.dirname(D)), "data", "taxonomy.json") if os.path.exists(os.path.join(os.path.dirname(os.path.dirname(D)), "data", "taxonomy.json")) else os.path.join(D, "taxonomy.json")), encoding="utf-8"))["tree"] for c in n["children"]}
def today(): return dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).date().isoformat()
def norm_title(t):
    t = unicodedata.normalize("NFD", t.lower()); t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", t.replace("đ", "d")).strip()
def norm_url(u):
    u = re.sub(r"^https?://(www\.)?", "", (u or "").strip()); u = re.sub(r"[?#].*$", "", u) if "news.google" not in u else u
    return u.rstrip("/").lower()
def score(it):
    s = it.get("scores") or {}
    if not s: return it.get("score", 0)
    return round(sum(W[k] * float(s.get(k, 0)) for k in W) / 5 * 100, 1)
def validate(it, kind):
    for f in ("title", "summary", "date"):
        if not it.get(f): raise ValueError(f"{kind} item missing '{f}': {it.get('title')}")
    if not it.get("sources") or not all(s.get("url", "").startswith("http") for s in it["sources"]):
        raise ValueError(f"item needs sources[].url: {it['title']}")
    tax = it.get("tax") or []
    if isinstance(tax, str): tax = it["tax"] = [tax]
    bad = [t for t in tax if t not in TAX]
    if not tax or bad: raise ValueError(f"item '{it['title']}' needs tax = list of level-2 ids from taxonomy.json, bad: {bad or 'missing'}")
    n, c = TAX[tax[0]]; it["category"] = c["name"]; it["l1"] = n["id"]
def load(name):
    p = os.path.join(D, name); return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"items": []}
def merge(db, items, kind):
    by_url = {norm_url(x["sources"][0]["url"]): x for x in db["items"]}  # dedupe on primary source URL + normalized title
    by_title = {norm_title(x["title"]): x for x in db["items"]}
    added = updated = 0
    for it in items:
        validate(it, kind)
        it.setdefault("added", today()); it.setdefault("origin", "manual"); it["type"] = kind
        it["id"] = it.get("id") or hashlib.sha1(norm_url(it["sources"][0]["url"]).encode()).hexdigest()[:12]
        if kind == "trend": it["score"] = score(it)
        old = by_url.get(norm_url(it["sources"][0]["url"])) or by_title.get(norm_title(it["title"]))
        if old:
            if it.get("origin") == "rss" and old.get("origin") == "manual": continue  # never let feeds overwrite curated items
            urls = {norm_url(s["url"]) for s in old["sources"]}
            srcs = old["sources"] + [s for s in it["sources"] if norm_url(s["url"]) not in urls]
            first = old.get("added"); old.update(it); old["sources"] = srcs; old["added"] = first; old["id"] = old.get("id") or it["id"]
            old["updated"] = today(); updated += 1
        else:
            db["items"].append(it); added += 1
            by_url[norm_url(it["sources"][0]["url"])] = it
            by_title[norm_title(it["title"])] = it
    return added, updated
def main(paths):
    T, M = load("trends.json"), load("market.json"); tot = {"trend": [0, 0], "market": [0, 0]}
    for p in paths:
        raw = json.load(open(p, encoding="utf-8"))
        groups = {"trend": raw.get("trends", []), "market": raw.get("market", [])} if isinstance(raw, dict) else \
                 {"trend": [x for x in raw if x.get("type", "trend") == "trend"], "market": [x for x in raw if x.get("type") == "market"]}
        for k, db in (("trend", T), ("market", M)):
            a, u = merge(db, groups[k], k); tot[k][0] += a; tot[k][1] += u
    for db, name, key in ((T, "trends.json", lambda x: (-x.get("score", 0), x["date"])), (M, "market.json", lambda x: x["date"])):
        db["items"].sort(key=key, reverse=(name == "market.json"))
        if name == "trends.json": db["items"].sort(key=lambda x: -x.get("score", 0))
        db["updated"] = dt.datetime.now(dt.timezone(dt.timedelta(hours=7))).isoformat(timespec="minutes"); db["count"] = len(db["items"])
        json.dump(db, open(os.path.join(D, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"trends: +{tot['trend'][0]} new, {tot['trend'][1]} updated, total {len(T['items'])} | "
          f"market: +{tot['market'][0]} new, {tot['market'][1]} updated, total {len(M['items'])}")
if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1:])
