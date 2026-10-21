"""v3 journeys (SCM, Nhà thầu & CĐT, phân khúc, bê tông M400, hero) at 360/390/768/1366 + overflow check on every page.
Usage: python trends/test_v3.py [base_url]  → screenshots/v3_*.png"""
import sys, os
from playwright.sync_api import sync_playwright
B = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/").rstrip("/") + "/"
S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots"); os.makedirs(S, exist_ok=True)
R = []; errs = []
def ok(n, c, i=""): R.append((n, bool(c))); print(("PASS " if c else "FAIL ") + n, i)
PAGES = ["index.html", "gia.html", "forecast.html", "xu-huong.html", "thi-truong.html", "scm.html", "nha-thau.html", "thang.html", "danh-muc.html?c=xd.be-tong", "mat-hang.html?id=rmc_hn_btHN_m400"]
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (1366, 768, 390, 360):
        m = w < 800; pg = b.new_page(viewport=dict(width=w, height=900 if not m else 800), is_mobile=w < 500)
        pg.on("pageerror", lambda e, w=w: errs.append(f"{w}: {e}"))
        sh = lambda n: pg.screenshot(path=f"{S}/v3_{w}_{n}.png", full_page=w in (1366, 390))
        for u in PAGES:
            pg.goto(B + u); pg.wait_for_selector(".hn-bar"); pg.wait_for_timeout(700)
            ov = pg.evaluate("document.documentElement.scrollWidth - innerWidth"); ok(f"{w} no h-overflow {u}", ov <= 1, ov)
            ok(f"{w} title+favicon {u}", pg.title() and pg.locator("link[rel=icon]").count() >= 1, pg.title()[:30])
        pg.goto(B + "index.html"); pg.wait_for_selector(".hk"); pg.wait_for_timeout(500); sh("01_home")
        ok(f"{w} hero KPIs", pg.locator(".hk").count() == 6); ok(f"{w} hero sparklines", pg.locator(".hk polyline").count() >= 3)
        ok(f"{w} home SCM widget", pg.locator("#scmw tr").count() >= 15); ok(f"{w} home org widget", pg.locator("#orgl li").count() >= 5)
        pg.click("#orgseg button[data-k=developer]"); ok(f"{w} home org→developer", pg.locator("#orgl li").count() >= 5)
        if m: pg.click(".hn-burger"); pg.wait_for_timeout(300); sh("02_menu_open"); ok(f"{w} burger shows SCM link", pg.locator(".hn-links.open a[href='scm.html']").is_visible())
        pg.goto(B + "scm.html"); pg.wait_for_selector("#ov tr td"); sh("03_scm")
        ok(f"{w} scm 14 rows", pg.locator("#ov tr").count() == 15)
        pg.locator("#sf button").nth(3).click(); n = pg.locator("#ov tr").count() - 1; ok(f"{w} scm signal filter", 0 < n < 14, n); pg.locator("#sf button").first.click()
        pg.locator("#ov a[data-c=thang-may]").click(); pg.wait_for_timeout(500); ok(f"{w} scm detail elevator", "Thang máy" in pg.inner_text("#detail h2")); sh("04_scm_detail")
        pg.select_option("#k-cat", "nhom-kinh"); pg.wait_for_timeout(200); t0 = pg.inner_text("#k-out")
        ok(f"{w} calc renders", "Giá về kho chưa VAT" in t0 and "So với giá mua trong nước" in t0)
        pg.fill("#k-ad", "35.58"); t1 = pg.inner_text("#k-out"); ok(f"{w} calc reacts to anti-dumping", t1 != t0)
        pg.locator("#calc").scroll_into_view_if_needed(); pg.screenshot(path=f"{S}/v3_{w}_05_calc.png")
        pg.goto(B + "nha-thau.html"); pg.wait_for_selector("#ed .card"); sh("06_contractors")
        n0 = pg.locator("#ed .card").count(); pg.locator("#orgs .chip", has_text="Coteccons").first.click(); n1 = pg.locator("#ed .card").count()
        ok(f"{w} contractor filter Coteccons", 0 < n1 < n0, f"{n0}->{n1}"); ok(f"{w} contractor URL state", "org=Coteccons" in pg.url)
        pg.click("#tabs button[data-k=developer]"); pg.wait_for_timeout(200); ok(f"{w} developer tab", pg.locator("#ed .card").count() >= 10); sh("07_developers")
        pg.select_option("#mseg", "hang-sang"); ok(f"{w} developer segment filter", pg.locator("#ed .card").count() >= 3)
        pg.goto(B + "thi-truong.html"); pg.wait_for_selector(".segtbl"); sh("08_market_segments")
        pg.locator("#sgc .chip", has_text="Biệt thự").click(); ok(f"{w} segment switch villas", "247" in pg.inner_text("#sgd"))
        pg.locator("#sg-go").click(); pg.wait_for_timeout(300); ok(f"{w} segment → news filter", pg.eval_on_selector("#ms", "e=>e.value") == "thap-tang")
        pg.goto(B + "danh-muc.html?c=xd.be-tong&tab=cmp"); pg.wait_for_selector("#pane .card"); sh("09_concrete_hn_hcm")
        ok(f"{w} concrete M400 pair", "M400" in pg.inner_text("#pane")); pg.click("#tabs button[data-k=scm]"); ok(f"{w} category SCM tab", "Khuyến nghị nguồn" in pg.inner_text("#pane")); sh("10_category_scm_tab")
        pg.close()
    b.close()
ok("no JS errors", not errs, errs[:3])
print(f"{sum(c for _, c in R)}/{len(R)} passed"); sys.exit(0 if all(c for _, c in R) else 1)
