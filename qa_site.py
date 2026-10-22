"""Site-wide audit + regression: python qa_site.py BASE_URL [--shots]
Asserts each shared component mounts exactly once per page, no console/page errors,
no horizontal overflow, no broken internal links, no mojibake in Vietnamese text."""
import sys, re, glob, os, urllib.request
from playwright.sync_api import sync_playwright
B = sys.argv[1].rstrip("/") + "/"
PAGES = sorted(os.path.basename(f) for f in glob.glob(os.path.join(os.path.dirname(__file__), "site", "*.html")))
W = [360, 390, 768, 1366, 1440, 1920]
ONCE = {"nav bar": ".hn-bar", "views widget": ".hn-views-wrap", "views pill": ".hn-views", "views chart": "#hn-vchart", "mega menu": ".mega"}
MAXONE = {"footer": "#foot"}
fails, checked = [], set()
def link_ok(u):
    try: return urllib.request.urlopen(urllib.request.Request(u, method="HEAD"), timeout=20).status < 400
    except Exception:
        try: return urllib.request.urlopen(u, timeout=20).status < 400
        except Exception: return False
with sync_playwright() as p:
    br = p.chromium.launch()
    for w in W:
        ctx = br.new_context(viewport={"width": w, "height": 900})
        for f in PAGES:
            pg = ctx.new_page(); errs = []
            pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(B + f, wait_until="networkidle", timeout=90000); pg.wait_for_timeout(2500)
            pg.evaluate("() => { const b = document.querySelector('.hn-views'); if (b) b.click(); }"); pg.wait_for_timeout(1500)
            r = pg.evaluate("""(sel) => { const c = {}; for (const k in sel) c[k] = document.querySelectorAll(sel[k]).length;
              const t = document.body.innerText; return {c, ov: document.documentElement.scrollWidth - innerWidth,
              moj: (t.match(/Ã[\\u0080-\\u00BF]|Æ[\\u0080-\\u00BF]|á»|áº|Ä‘|Â·|\\uFFFD/g) || []).slice(0, 3), tip: (document.querySelector('.vc-tip')||{}).textContent || "",
              links: [...new Set([...document.querySelectorAll('a[href]')].map(a => a.href).filter(h => h.startsWith(location.origin)).map(h => h.split('#')[0]))]}; }""", {**ONCE, **MAXONE})
            for k in ONCE:
                if k.startswith("views") and r["c"][k] == 0: continue  # widget hides itself if counter API unreachable
                if r["c"][k] != 1: fails.append((w, f, f"{k} x{r['c'][k]}"))
            if r["c"]["footer"] > 1: fails.append((w, f, f"footer x{r['c']['footer']}"))
            if r["ov"] > 0: fails.append((w, f, f"overflow {r['ov']}px"))
            if r["moj"]: fails.append((w, f, f"mojibake {r['moj']}"))
            if "chưa đo" in r["tip"]: fails.append((w, f, "stale tooltip"))
            errs = [e for e in errs if "zgo.at" not in e and "goatcounter" not in e.lower()]
            if errs: fails.append((w, f, "console: " + " | ".join(errs[:3])))
            for u in r["links"]:
                if u not in checked:
                    checked.add(u)
                    if not link_ok(u): fails.append((w, f, "broken link " + u))
            pg.close()
        ctx.close()
    br.close()
print(f"pages={len(PAGES)} widths={W} links_checked={len(checked)}")
for x in fails: print("FAIL", *x)
print("ALL OK" if not fails else f"{len(fails)} failures"); sys.exit(1 if fails else 0)
