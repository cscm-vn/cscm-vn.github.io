"""Headless journey test of the hub (desktop + mobile). Usage: python trends/test_ui.py [base_url]"""
import sys, os, json
from playwright.sync_api import sync_playwright
B = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8765/").rstrip("/") + "/"
S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "screenshots"); os.makedirs(S, exist_ok=True)
R = []; errs = []
def ok(name, cond, info=""): R.append((name, bool(cond), info)); print(("PASS " if cond else "FAIL ") + name, info)
with sync_playwright() as p:
    b = p.chromium.launch()
    for mode, vp in (("desktop", dict(width=1366, height=900)), ("mobile", dict(width=390, height=844))):
        pg = b.new_page(viewport=vp, is_mobile=mode == "mobile")
        pg.on("pageerror", lambda e: errs.append(f"{mode}: {e}")); pg.on("console", lambda m: m.type == "error" and errs.append(f"{mode} console: {m.text}"))
        sh = lambda n: pg.screenshot(path=f"{S}/trends_{mode}_{n}.png", full_page=mode == "desktop")
        pg.goto(B + "index.html"); pg.wait_for_selector("#top5 .card"); sh("01_home")
        ok(f"{mode} home top5", pg.locator("#top5 .card").count() == 5); ok(f"{mode} home tiles", pg.locator("#tiles .tile").count() >= 7)
        ok(f"{mode} home HN/HCM", pg.locator("#cmp .card").count() >= 1); ok(f"{mode} home movers", pg.locator("#movers tr").count() > 1)
        if mode == "desktop":
            pg.click(".hn-mega-btn"); pg.wait_for_selector(".mega.open"); sh("02_mega_menu")
            pg.click(".mega a[href='danh-muc.html?c=xd.cot-thep']")
        else:
            pg.goto(B + "danh-muc.html?c=xd.cot-thep")
        pg.wait_for_selector("#pt tr"); ok(f"{mode} category steel rows", pg.locator("#pt tr").count() > 20, pg.locator("#pt tr").count())
        ok(f"{mode} breadcrumb", "Xây dựng" in pg.inner_text("#crumb")); sh("03_category_steel")
        pg.fill("#q", "hoa phat cb300"); n = pg.locator("#pt tr").count(); ok(f"{mode} category filter", 1 < n < 6, n)
        if pg.locator("#rg button").count(): pg.locator("#rg button").nth(1).click()
        pg.click("#tabs button[data-k=cmp]"); pg.wait_for_selector(".ins"); sh("04_category_hn_hcm"); ok(f"{mode} HN/HCM tab", pg.locator(".ins").count() >= 4)
        pg.click("#tabs button[data-k=trend]"); ok(f"{mode} cat trends tab", pg.locator("#pane .card").count() >= 1)
        pg.goto(B + "mat-hang.html?id=lme_copper"); pg.wait_for_selector("canvas"); pg.wait_for_timeout(600); sh("05_item_copper")
        ok(f"{mode} item monthly table", pg.locator("table.t tr").count() > 2)
        pg.goto(B + "mat-hang.html?id=vnsteel_hoa_phat_mien_bac_cb300_d10"); pg.wait_for_selector("h1"); sh("06_item_steel_hn")
        ok(f"{mode} item steel HN/HCM", "TP.HCM" in pg.inner_text("main"))
        pg.goto(B + "xu-huong.html"); pg.wait_for_selector("#list .card"); n0 = pg.locator("#list .card").count(); sh("07_trends")
        pg.locator("#l1 .chip").nth(1).click(); n1 = pg.locator("#list .card").count(); ok(f"{mode} trends L1 filter", 0 < n1 < n0, f"{n0}->{n1}")
        pg.locator("#l1 .chip").first.click(); pg.fill("#q", "phật sơn"); n2 = pg.locator("#list .card").count(); ok(f"{mode} trends search accent-insensitive", n2 >= 1, n2); sh("08_trends_search")
        links = pg.eval_on_selector_all("#list a[target=_blank]", "els=>els.map(e=>e.href)"); ok(f"{mode} trend links http", links and all(l.startswith("http") for l in links), len(links))
        pg.goto(B + "thi-truong.html"); pg.wait_for_selector("#list .card"); sh("09_market")
        pg.locator("#rg button[data-r='TP.HCM']").click(); ok(f"{mode} market region filter", all("TP.HCM" in t for t in pg.locator("#list .card .pill:first-child").all_inner_texts()))
        pg.goto(B + "thang.html"); pg.wait_for_selector("#cat tr"); sh("10_monthly"); ok(f"{mode} monthly table", pg.locator("#cat tr").count() > 1)
        pg.goto(B + "gia.html"); pg.wait_for_selector(".hn-bar"); pg.wait_for_timeout(800); sh("11_price_table_with_nav"); ok(f"{mode} gia.html nav", pg.locator(".hn-bar").count() == 1)
        pg.goto(B + "forecast.html"); pg.wait_for_selector(".hn-bar"); pg.wait_for_timeout(1200); sh("15_forecast_with_nav"); ok(f"{mode} forecast nav", pg.locator(".hn-bar").count() == 1)
        pg.goto(B + "danh-muc.html?c=xd.be-tong&tab=fc"); pg.wait_for_selector("#pane"); pg.wait_for_timeout(300); sh("16_category_forecast"); ok(f"{mode} category forecast tab", pg.locator("#pane table tr").count() > 1)
        pg.goto(B + "index.html"); pg.wait_for_selector(".hn-search input")
        if mode == "mobile": pass
        pg.fill(".hn-search input", "xi mang pcb40"); pg.wait_for_selector(".hn-res a"); sh("12_global_search"); ok(f"{mode} global search", pg.locator(".hn-res a").count() >= 3)
        if mode == "mobile":
            pg.click(".hn-burger"); pg.wait_for_timeout(200); sh("13_burger"); ok("mobile burger opens", pg.locator(".hn-links.open").count() == 1)
            pg.goto(B + "danh-muc.html?c=ht.tbvs"); pg.wait_for_selector("#pane"); sh("14_cat_tbvs_mobile")
            ok("mobile no horizontal overflow", pg.evaluate("document.documentElement.scrollWidth <= innerWidth + 2"), pg.evaluate("[document.documentElement.scrollWidth, innerWidth]"))
        pg.close()
    b.close()
print("JS errors:", errs or "none"); print(f"{sum(r[1] for r in R)}/{len(R)} passed")
json.dump(dict(results=R, errors=errs), open(os.path.join(S, "trends_test_results.json"), "w"), ensure_ascii=False, indent=1)
