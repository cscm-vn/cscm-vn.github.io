"""Kiểm thử headless: python forecast/test_ui.py http://localhost:8765/forecast.html <outdir>"""
import sys
from playwright.sync_api import sync_playwright
url, out = sys.argv[1], sys.argv[2]; errs = []
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1400, "height": 900})
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(url); pg.wait_for_selector("#tbl tbody tr.row", timeout=20000)
    n = pg.locator("#tbl tbody tr.row").count(); print("rows", n)
    pg.screenshot(path=f"{out}/forecast_01_top.png")
    pg.screenshot(path=f"{out}/forecast_02_full.png", full_page=True)
    pg.click("#scen button[data-s=bull]"); r_bull = pg.locator("#tbl tbody tr.row").first.inner_text()
    pg.click("#scen button[data-s=bear]"); r_bear = pg.locator("#tbl tbody tr.row").first.inner_text()
    assert r_bull != r_bear, "scenario toggle has no effect"
    pg.click("#scen button[data-s=base]")
    pg.fill("#q", "dong"); print("search dong ->", pg.locator("#tbl tbody tr.row").count()); 
    pg.locator("#tbl tbody tr.row").first.click(); pg.wait_for_timeout(500)
    pg.locator("#chTitle").scroll_into_view_if_needed(); pg.screenshot(path=f"{out}/forecast_03_chart_copper.png")
    pg.fill("#q", ""); pg.click("text=Xây dựng › Bê tông thương phẩm"); print("concrete rows", pg.locator("#tbl tbody tr.row").count())
    pg.locator("#tbl").scroll_into_view_if_needed(); pg.screenshot(path=f"{out}/forecast_04_taxonomy_concrete.png")
    pg.locator("#hnhcm").scroll_into_view_if_needed(); pg.screenshot(path=f"{out}/forecast_05_hn_vs_hcm.png")
    print("pairs", pg.locator("#pairs tbody tr").count())
    pg.locator("#mep").scroll_into_view_if_needed(); pg.screenshot(path=f"{out}/forecast_06_mep.png")
    pg.locator("#drivers").scroll_into_view_if_needed(); pg.screenshot(path=f"{out}/forecast_07_drivers.png")
    pg.fill("#qty", "300000"); pg.select_option("#sreg", "HCM"); pg.locator("#strategy").scroll_into_view_if_needed(); pg.wait_for_timeout(300)
    print("strategy:", pg.locator("#stT tbody").inner_text()[:400])
    pg.screenshot(path=f"{out}/forecast_08_strategy.png")
    pg.locator("#method").scroll_into_view_if_needed(); pg.screenshot(path=f"{out}/forecast_09_backtest.png")
    m = b.new_page(viewport={"width": 390, "height": 844}); m.goto(url); m.wait_for_selector("#tbl tbody tr.row"); m.screenshot(path=f"{out}/forecast_10_mobile.png")
    b.close()
print("JS errors:", errs or "none")
