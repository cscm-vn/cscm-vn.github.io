"""QA for hop-dong.html + shared nav overflow on every page. Usage: python qa.py BASE_URL [--shots]"""
import sys, json, re
from playwright.sync_api import sync_playwright
B = sys.argv[1].rstrip("/") + "/"; SHOTS = "--shots" in sys.argv
PAGES = ["index.html","gia.html","dieu-chinh.html","forecast.html","xu-huong.html","thi-truong.html","scm.html","nha-thau.html","thang.html","hop-dong.html","huong-dan.html","danh-muc.html"]
W = [360, 390, 768, 1181, 1280, 1366, 1440, 1600, 1920]
bad = []
with sync_playwright() as p:
    br = p.chromium.launch()
    _np = br.new_page; _nc = br.new_context
    def NP(**k):
        pg = _np(**k); pg.route("**/*zgo.at/**", lambda r: r.abort()); return pg
    def NC(**k):
        c = _nc(**k); c.route("**/*zgo.at/**", lambda r: r.abort()); return c
    br.new_page = NP; br.new_context = NC
    for w in W:
        pg = br.new_page(viewport={"width": w, "height": 900})
        for f in PAGES:
            pg.goto(B + f, wait_until="domcontentloaded", timeout=60000); pg.wait_for_timeout(1200)
            r = pg.evaluate("""() => { const d = document.documentElement, n = document.querySelector('.hn-in'), l = document.querySelector('.hn-links');
              const ln = l ? [...l.children].filter(e => e.offsetParent) : []; const tops = new Set(ln.map(e => Math.round(e.getBoundingClientRect().top)));
              const has = !!document.querySelector('.hn-links a[href="hop-dong.html"]');
              return {doc: d.scrollWidth - innerWidth, nav: n ? n.scrollWidth - n.clientWidth : 0, rows: getComputedStyle(l||document.body).display === 'none' ? 0 : (l.getBoundingClientRect().height < 48 ? 1 : 2), has,
                      right: ln.length ? Math.max(...ln.map(e => e.getBoundingClientRect().right)) - innerWidth : 0}; }""")
            ok = r["doc"] <= 0 and r["nav"] <= 0 and r["has"] and (w <= 1180 or r["rows"] == 1) and r["right"] <= 0
            if not ok: bad.append((w, f, r))
        pg.close()
    print("overflow/nav issues:", bad or "none")
    # functional QA of the new page
    for w, tag in ((1440, "desktop"), (390, "mobile")):
        ctx = br.new_context(viewport={"width": w, "height": 900}, timezone_id="Asia/Ho_Chi_Minh"); pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
        pg.goto(B + "hop-dong.html", wait_until="domcontentloaded"); pg.wait_for_selector("#legal .it"); pg.wait_for_timeout(2500)
        cnt = pg.evaluate("""() => ({legal: document.querySelectorAll('#legal .it').length, fidic: document.querySelectorAll('#fidic-l .it').length, trade: document.querySelectorAll('#trade .it').length,
            disp: document.querySelectorAll('#disp .it').length, ck: document.querySelectorAll('#ck li').length, feed: document.querySelectorAll('#feed li a').length, q: document.querySelectorAll('#qz .qi').length,
            h1font: getComputedStyle(document.querySelector('h1')).fontFamily, nfc: document.body.innerText === document.body.innerText.normalize('NFC'),
            lora: document.fonts.check('600 20px Lora', 'Hợp đồng ữ ặ ố'), activeNav: document.querySelector('.hn-links a.on')?.getAttribute('href')})""")
        print(tag, cnt, "errors:", errs)
        if SHOTS:
            pg.screenshot(path=f"screenshots/hopdong_{tag}_top.png"); pg.screenshot(path=f"screenshots/hopdong_{tag}_full.png", full_page=True)
        # answer quiz: click first option of each question, check score & persistence
        for i in range(5): pg.locator("#qz .qi").nth(i).locator(".opt").first.click(); pg.wait_for_timeout(80)
        sc = pg.inner_text("#qz-score"); st = pg.inner_text("#qz-streak"); pg.reload(wait_until="domcontentloaded"); pg.wait_for_selector("#qz .qi"); sc2 = pg.inner_text("#qz-score")
        print(tag, "quiz score", sc, "streak", st, "after reload", sc2, "explanations", pg.locator("#qz .ex").count())
        if SHOTS: pg.locator("#qz").screenshot(path=f"screenshots/hopdong_{tag}_quiz.png")
        # rotation: different questions on other days
        q = lambda: pg.evaluate("() => [...document.querySelectorAll('#qz .q')].map(e => e.textContent.slice(7, 50)).join('|')")
        today = q(); seen = {today}
        for dd in (1, 2, 7, 13, 14):
            pg.clock.install(time=__import__('datetime').datetime(2026, 10, 22 + dd if 22 + dd <= 31 else 31, 12, 0)) if False else None
        ctx.close()
    # rotation check by fixed clock on several days
    sets = []
    for day in ["2026-10-22T10:00:00+07:00", "2026-10-23T00:30:00+07:00", "2026-10-24T23:50:00+07:00", "2026-11-05T10:00:00+07:00"]:
        ctx = br.new_context(timezone_id="Asia/Ho_Chi_Minh"); pg = ctx.new_page(); pg.clock.install(time=day)
        pg.goto(B + "hop-dong.html", wait_until="domcontentloaded"); pg.wait_for_selector("#qz .qi", timeout=30000)
        sets.append((day, pg.evaluate("() => [...document.querySelectorAll('#qz .qi')].map(e => e.dataset.q).join(',')"))); ctx.close()
    print("rotation:", sets, "distinct:", len({s for _, s in sets}))
    if SHOTS:
        pg = br.new_page(viewport={"width": 1440, "height": 900}); pg.goto(B + "hop-dong.html#pvtm", wait_until="domcontentloaded"); pg.wait_for_timeout(800)
        pg.locator("#pvtm").screenshot(path="screenshots/hopdong_desktop_trade.png")
        pg.goto(B + "huong-dan.html#hop-dong", wait_until="domcontentloaded"); pg.wait_for_timeout(500); pg.screenshot(path="screenshots/hopdong_huongdan.png")
        pg = br.new_page(viewport={"width": 360, "height": 800}); pg.goto(B + "hop-dong.html", wait_until="domcontentloaded"); pg.click(".hn-burger"); pg.wait_for_timeout(300); pg.screenshot(path="screenshots/hopdong_mobile360_menu.png")
    br.close()
