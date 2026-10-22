"""Landed-cost China vs Vietnam builder (SCM tab).
Source of truth: trends/data/landed-cost.json (editorial: items, taxes, prices, sources, assumptions).
This script refreshes FX automatically (Hub price board USD/VND + open.er-api.com USD/CNY), flags stale freight,
computes baseline results per item × region with the SAME formula as scm.html, and writes site/data/landed-cost.json.
Usage: python trends/landed.py [--site site] [--write-source]"""
import json, os, sys, datetime as dt, urllib.request, unicodedata
H = os.path.dirname(os.path.abspath(__file__)); SRC = os.path.join(H, "data", "landed-cost.json")
TZ = dt.timezone(dt.timedelta(hours=7))
def load(p):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return None
def fetch_json(u):
    try: return json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read())
    except Exception as e: print("fx fetch failed:", e); return None
def compute(d, it, region, fx=None, frt_mult=1.0, fob=None, local=None):
    fx = fx or d["fx"]["usd_vnd"]; c = it["cont"].replace("GP", "").replace("HQ", ""); ck = "d" + c
    q = max(it["qty"]["v"], 1); t = it["tax"]
    fob = it["fob"]["mid"] if fob is None else fob
    fr = d["freight"][region][ck] * frt_mult / q
    ins = (fob + fr) * d["ins_pct"]["v"] / 100; cif = fob + fr + ins
    rate = min(x for x in (t["mfn"], t["acfta"]) if x is not None)
    duty = cif * rate / 100; ad = cif * (it.get("ad_pct") or 0) / 100
    base = (cif + duty + ad) * fx
    port = (d["port"]["thc_usd"][ck] * fx + d["port"]["do_vnd"] + d["port"]["broker_vnd"] + it["inspect"]["v"]) / q
    truck = d["truck"][region][ck] / q
    brk = base * it["breakage"]["v"] / 100; fin = base * d["fin_pct"]["v"] / 100 * it["lead"]["v"] / 365
    landed = base + port + truck + brk + fin + it["extra"]["v"]
    lm = it["local"]["mid"] if local is None else local
    lex = (lm / (1 + t["vat"] / 100) if it["local"]["vat_incl"] else lm) * (1 - it["disc"]["v"] / 100) + d["local_delivery"]["v"]
    return dict(fob=fob * fx, freight=fr * fx, ins=ins * fx, cif=cif * fx, duty_rate=rate, duty=duty * fx, ad=ad * fx, port=port, truck=truck,
                breakage=brk, finance=fin, extra=it["extra"]["v"], landed=landed, import_vat=(cif + duty + ad) * fx * t["vat"] / 100,
                local=lex, saving=1 - landed / lex)
def verdict(d, s):
    th = d["thresholds"]; return "co-hoi" if s * 100 >= th["opp"] else "can-nhac" if s * 100 >= th["consider"] else "noi-dia"
def main():
    a = sys.argv[1:]; site = a[a.index("--site") + 1] if "--site" in a else os.path.join(os.path.dirname(H), "site")
    d = load(SRC); now = dt.datetime.now(TZ)
    hub = load(os.path.join(site, "data", "hub.json")) or {}
    er = fetch_json("https://open.er-api.com/v6/latest/USD")
    if hub.get("usd_vnd"): d["fx"]["usd_vnd"] = round(hub["usd_vnd"])
    elif er: d["fx"]["usd_vnd"] = round(er["rates"]["VND"])
    if er: d["fx"]["cny_vnd"] = round(d["fx"]["usd_vnd"] / er["rates"]["CNY"], 1)
    d["fx"]["asof"] = (hub.get("updated") or now.isoformat(timespec="minutes"))[:16]
    d["fx"]["text"] = ("USD/VND từ Bảng giá Hub" if hub.get("usd_vnd") else "USD/VND từ open.er-api.com") + (" · USD/CNY từ open.er-api.com" if er else " · USD/CNY lần cập nhật trước")
    fa = d["freight"]["src"].get("date", "")
    try: d["freight"]["stale"] = (now.date() - dt.date.fromisoformat(fa + "-01" if len(fa) == 7 else fa)).days > 45
    except Exception: d["freight"]["stale"] = True
    res = {}
    for it in d["items"]:
        r = {}
        for reg in ("hn", "hcm"):
            b = compute(d, it, reg)
            sens = dict(fx_up=compute(d, it, reg, fx=d["fx"]["usd_vnd"] * 1.05)["saving"], fx_dn=compute(d, it, reg, fx=d["fx"]["usd_vnd"] * 0.95)["saving"],
                        frt_x2=compute(d, it, reg, frt_mult=2)["saving"],
                        worst=compute(d, it, reg, fob=it["fob"]["hi"], local=it["local"]["lo"])["saving"], best=compute(d, it, reg, fob=it["fob"]["lo"], local=it["local"]["hi"])["saving"])
            r[reg] = dict(landed=round(b["landed"]), local=round(b["local"]), saving=round(b["saving"], 4), verdict=verdict(d, b["saving"]), sens={k: round(v, 4) for k, v in sens.items()})
        res[it["id"]] = r
    d["results"] = res; d["built"] = now.isoformat(timespec="minutes")
    txt = unicodedata.normalize("NFC", json.dumps(d, ensure_ascii=False, separators=(",", ":")))
    os.makedirs(os.path.join(site, "data"), exist_ok=True); open(os.path.join(site, "data", "landed-cost.json"), "w", encoding="utf-8").write(txt)
    if "--write-source" in a:
        open(SRC, "w", encoding="utf-8").write(unicodedata.normalize("NFC", json.dumps(d, ensure_ascii=False, indent=1)))
    for it in d["items"]:
        r = res[it["id"]]; print(f'{it["id"]:16} HN {r["hn"]["landed"]:>12,} vs {r["hn"]["local"]:>12,} {r["hn"]["saving"]*100:6.1f}% {r["hn"]["verdict"]:9} | HCM {r["hcm"]["saving"]*100:6.1f}%')
    print("fx", d["fx"]["usd_vnd"], d["fx"]["cny_vnd"], "freight stale:", d["freight"]["stale"])
if __name__ == "__main__": main()
