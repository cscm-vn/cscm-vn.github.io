"""Site-wide audit + regression: python qa_site.py BASE_URL [--shots]
Asserts each shared component mounts exactly once per page, no console/page errors,
no horizontal overflow, no broken internal links, no mojibake in Vietnamese text."""
import sys, re, glob, os, urllib.request, urllib.parse
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
            if f == "index.html":  # điểm nóng nhóm: mỗi ô tối đa 1 khối .hl, khớp highlights.json, không tràn ô
                hq = pg.evaluate("""async () => { const t = [...document.querySelectorAll('#tiles .tile.hlt')]; let j = null;
                  try { j = await (await fetch('data/highlights.json', {cache: 'no-store'})).json(); } catch (e) {}
                  const want = j ? j.groups.filter(g => g.prices.length || g.news.length).map(g => g.id).sort() : null;
                  return {n: t.length, multi: t.filter(x => x.querySelectorAll('.hl').length > 1).map(x => x.dataset.g),
                    have: t.filter(x => x.querySelector('.hl')).map(x => x.dataset.g).sort(), want,
                    ov: t.filter(x => { const h = x.querySelector('.hl'); return h && (h.getBoundingClientRect().right > x.getBoundingClientRect().right + 1 || h.scrollWidth > h.clientWidth + 1); }).map(x => x.dataset.g)}; }""")
                if hq["n"] != 8: fails.append((w, f, f"category tiles x{hq['n']} (expect 8)"))
                if hq["want"] is None: fails.append((w, f, "highlights.json missing"))
                elif hq["have"] != hq["want"]: fails.append((w, f, f"highlights shown {hq['have']} != data {hq['want']}"))
                if hq["multi"]: fails.append((w, f, f"highlight block duplicated in {hq['multi']}"))
                if hq["ov"]: fails.append((w, f, f"highlight overflow in {hq['ov']}"))
            if f == "index.html":  # ⚖️ Luật & chính sách mới: đúng 1 section, ở cuối (ngay trước footer), 5–6 thẻ, link hợp lệ, không tràn
                pq = pg.evaluate("""() => { const s = document.querySelectorAll('#policy'), el = s[0]; if (!el) return {n: 0};
                  const cards = [...el.querySelectorAll('#pol > .card')], W = el.getBoundingClientRect().right + 1;
                  const nx = el.nextElementSibling, secs = [...document.querySelectorAll('#main > section, #main > .grid')];
                  return {n: s.length, k: cards.length, last: secs[secs.length - 1] === el && !!nx && nx.id === 'foot',
                    ext: cards.map(c => c.querySelector('a[href]')?.href || ''), more: [...el.querySelectorAll('a.pmore')].map(a => a.getAttribute('href')), all: el.querySelector('h2 a')?.getAttribute('href'),
                    ov: cards.filter(c => c.getBoundingClientRect().right > W || c.scrollWidth > c.clientWidth + 1).length}; }""")
                if pq["n"] != 1: fails.append((w, f, f"policy section x{pq['n']}"))
                else:
                    if not 5 <= pq["k"] <= 6: fails.append((w, f, f"policy items x{pq['k']} (expect 5-6)"))
                    if not pq["last"]: fails.append((w, f, "policy section not last before footer"))
                    if pq["all"] != "hop-dong.html#chinh-sach": fails.append((w, f, f"policy 'xem tất cả' href {pq['all']}"))
                    if pq["ov"]: fails.append((w, f, f"policy overflow in {pq['ov']} cards"))
                    if w == W[0]:  # dữ liệu: 1 tin/cụm, ≤2/chủ đề, khớp số thẻ; link '+N tin' trỏ đúng cụm có trên hop-dong
                        import json as _js
                        _p = _js.load(urllib.request.urlopen(B + "data/policy-feed.json", timeout=30)); _I = {x["id"]: x for x in _p["items"]}; _H = [_I[h["id"]] for h in _p["home"] if h["id"] in _I]
                        if len(_H) != pq["k"]: fails.append((w, f, f"policy cards {pq['k']} != home data {len(_H)}"))
                        if len({x["cluster"] for x in _H}) != len(_H): fails.append((w, f, "policy home duplicate cluster"))
                        if max([sum(1 for y in _H if y["topics"][0] == x["topics"][0]) for x in _H] or [0]) > 2: fails.append((w, f, "policy home >2 per topic"))
                        for m in pq["more"]:
                            c = urllib.parse.unquote(m.split("pc=")[1].split("#")[0]) if "pc=" in m else ""
                            if c not in _p["clusters"] or not m.startswith("hop-dong.html?pc="): fails.append((w, f, "policy bad cluster link " + m))
                    for u in pq["ext"]:
                        if not u.startswith("https://"): fails.append((w, f, "policy bad link " + u))
                        elif w == W[0] and not link_ok(u): fails.append((w, f, "policy broken link " + u))
            if f == "hop-dong.html":
                hq2 = pg.evaluate("""() => ({n: document.querySelectorAll('#chinh-sach').length, k: document.querySelectorAll('#pf > li .score').length,
                  toc: document.querySelectorAll('.hd-toc a[href="#chinh-sach"]').length, chips: document.querySelectorAll('#pf-f button').length})""")
                if hq2["n"] != 1 or hq2["toc"] != 1: fails.append((w, f, f"policy section x{hq2['n']} toc x{hq2['toc']}"))
                if hq2["k"] < 5: fails.append((w, f, f"policy list items x{hq2['k']}"))
                if hq2["chips"] < 2: fails.append((w, f, "policy topic chips missing"))
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
try:  # sanity: cùng thành phố & cùng cơ sở, mác cao hơn không được rẻ hơn mác thấp hơn
    import json as _j
    _h = _j.load(urllib.request.urlopen(B + "data/hub.json", timeout=30))
    _r = sorted([(int(re.search(r"M(\d+)", c["label"]).group(1)), c) for c in _h.get("compare", []) if c.get("basis") == "rmc" and re.search(r"M\d+", c["label"])], key=lambda t: t[0])
    for (g1, c1), (g2, c2) in zip(_r, _r[1:]):
        for reg in ("hn", "hcm"):
            if c2[reg] < c1[reg]: fails.append(("-", "hub.json", f"grade order {reg}: M{g2} {c2[reg]} < M{g1} {c1[reg]}"))
except Exception as e: fails.append(("-", "hub.json", f"grade-order check error: {e}"))
print(f"pages={len(PAGES)} widths={W} links_checked={len(checked)}")
for x in fails: print("FAIL", *x)
print("ALL OK" if not fails else f"{len(fails)} failures"); sys.exit(1 if fails else 0)
