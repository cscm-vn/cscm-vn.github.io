"""Site-wide audit + regression: python qa_site.py BASE_URL [--shots]
Asserts each shared component mounts exactly once per page, no console/page errors,
no horizontal overflow, no broken internal links, no mojibake in Vietnamese text."""
import sys, re, glob, os, json, urllib.request, urllib.parse
from playwright.sync_api import sync_playwright
B = sys.argv[1].rstrip("/") + "/"
PAGES = sorted(os.path.basename(f) for f in glob.glob(os.path.join(os.path.dirname(__file__), "site", "*.html")))
W = [360, 390, 768, 1366, 1440, 1920]
ONCE = {"nav bar": ".hn-bar", "views widget": ".hn-views-wrap", "views pill": ".hn-views", "views chart": "#hn-vchart", "mega menu": ".mega"}
MAXONE = {"footer": "#foot"}
fails, checked = [], set()

# ---- Nhà thầu & CĐT: bảng tra cứu nhà cung cấp (#ncc) ----
GOV_MANUAL = {"https://tracuunnt.gdt.gov.vn/tcnnt/mstdn.jsp", "https://dangkykinhdoanh.gov.vn", "https://muasamcong.mof.gov.vn", "https://www.gdt.gov.vn"}  # cổng nhà nước: một số mạng ngoài VN không mở được → chỉ kiểm đúng địa chỉ, không HEAD
# số liệu CTD năm tài chính 2026 (01/07/2025–30/06/2026) đọc tay từ BCTC hợp nhất đã kiểm toán, độc lập với suppliers.json (đơn vị đồng)
CTD_RAW = {"rev": 34339621317795, "gp": 1445893909484, "np": 788387654043, "cfo": 828951292295}
CTD_SHOW = ["34.340", "1.446", "788", "829", "38.696", "9.652", "15.326", "FY2026", "Theo dõi", "0303443233", "CTD"]
def ncc_checks(pg, w, f, fails):
    def F(m): fails.append((w, f, "ncc: " + m))
    n = pg.evaluate("() => [document.querySelectorAll('#ncc').length, document.querySelectorAll('#ncc-q').length, document.querySelectorAll('#ncc-out').length, document.querySelectorAll('#ncc h2').length]")
    if n != [1, 1, 1, 1]: return F(f"bảng không xuất hiện đúng 1 lần {n}")
    if not pg.evaluate("() => { const l = document.querySelector('label[for=ncc-q]'); return !!l && l.textContent.trim().length > 5; }"): F("ô tìm thiếu label")
    pos = pg.evaluate("() => { const a = document.querySelector('#ncc'), t = document.querySelector('#tabs'), s = document.querySelector('main .sub'); return !!t && !!s && !!(s.compareDocumentPosition(a) & 4) && !!(a.compareDocumentPosition(t) & 4); }")
    if not pos: F("sai vị trí (phải nằm giữa phụ đề trang và dải tab)")
    def ask(q, enter=True):
        pg.fill("#ncc-q", q); pg.wait_for_timeout(250)
        sug = pg.locator("#ncc-list li").all_inner_texts()
        if enter: pg.keyboard.press("Enter"); pg.wait_for_timeout(500)
        return sug, pg.locator("#ncc-out").inner_text()
    for q, first, legal in [("cotecon", "COTECCONS", "XÂY DỰNG COTECCONS"), ("coteccons", "COTECCONS", "XÂY DỰNG COTECCONS"), ("CTD", "COTECCONS", "XÂY DỰNG COTECCONS"), ("0303443233", "COTECCONS", "XÂY DỰNG COTECCONS"),
                            ("hoa phat", "HÒA PHÁT", "TẬP ĐOÀN HÒA PHÁT"), ("Hòa Phát", "HÒA PHÁT", "TẬP ĐOÀN HÒA PHÁT"), ("HPG", "HÒA PHÁT", "TẬP ĐOÀN HÒA PHÁT"), ("xay dung hoa binh", "HÒA BÌNH", "HÒA BÌNH")]:
        sug, txt = ask(q)
        if not sug or first not in sug[0].upper(): F(f"gợi ý đầu cho “{q}” = {sug[:1]}")
        if legal not in txt.upper(): F(f"thẻ cho “{q}” không có “{legal}”")
        if "kỳ" not in txt.lower() and "BCTC" not in txt: F(f"thẻ “{q}” thiếu kỳ báo cáo/BCTC")
    # thẻ Coteccons: số liệu khớp BCTC
    sug, txt = ask("coteccons")
    for k in CTD_SHOW:
        if k not in txt: F(f"thẻ Coteccons thiếu “{k}”")
    full = pg.locator("#ncc-out").text_content()  # gồm cả phần “Cách tính nhãn” đang gập
    for lab in ("Tốt", "Theo dõi", "Thận trọng"):
        if lab not in full: F(f"thẻ Coteccons không nêu ngưỡng nhãn “{lab}”")
    for k in ("chưa tra tự động", "tin chưa kiểm chứng" if "Tin gần đây" in txt else "chưa tra tự động"):
        if k.lower() not in txt.lower(): F(f"thẻ Coteccons thiếu cụm “{k}”")
    try:
        d = json.load(urllib.request.urlopen(B + "data/suppliers.json", timeout=30))
        u = next(x for x in d["units"] if x["mst"] == "0303443233"); v = u["fin"]["periods"][0]["v"]
        for k, x in CTD_RAW.items():
            if v[k] != x: F(f"suppliers.json CTD {k}={v[k]} ≠ BCTC {x}")
    except Exception as e: F(f"đọc suppliers.json lỗi {e}")
    # link nguồn trong thẻ
    ls = pg.evaluate("() => [...document.querySelectorAll('#ncc-out a[href]')].map(a => a.href)")
    pdfs = [u for u in ls if u.lower().split('?')[0].endswith('.pdf')]
    if not pdfs: F("thẻ Coteccons không có link BCTC gốc")
    for u in sorted(set(ls)):
        if u in GOV_MANUAL or not u.startswith("http"): continue
        host = urllib.parse.urlparse(u).netloc
        if u in pdfs or "coteccons.vn" in host and "/bao-cao-tai-chinh" in u or "api.vietqr.io" in host:
            if not link_ok(u): F("link nguồn hỏng " + u)
    ls = [u.rstrip("/") if u.count("/") == 3 else u for u in ls]
    man = {u for u in ls if "gdt.gov.vn" in u or "dangkykinhdoanh" in u or "muasamcong" in u}
    if not man <= GOV_MANUAL or len(man) < 3: F(f"link tra cứu thủ công sai {man}")
    # đơn vị chưa niêm yết
    sug, txt = ask("newtecons")
    if "Chưa có BCTC công khai" not in txt: F("Newtecons thiếu nhãn “Chưa có BCTC công khai”")
    if "Doanh thu thuần" in txt: F("Newtecons không được hiện doanh thu")
    # mở rộng dữ liệu (nhà thầu/nhà cung cấp hoàn thiện–nội thất–MEP): tên có/không dấu, viết tắt, MST, nhóm hạng mục
    for q, first, legal in [("An Cường", "AN CƯỜNG", "GỖ AN CƯỜNG"), ("ancuong", "AN CƯỜNG", "GỖ AN CƯỜNG"), ("pado", "PADO", "TNHH PADO"), ("thien son", "THIÊN SƠN", "NỘI THẤT THIÊN SƠN"),
                            ("daikin", "DAIKIN", "DAIKIN AIR CONDITIONING"), ("0301450108", "DAIKIN", "DAIKIN AIR CONDITIONING"), ("schindler", "SCHINDLER", "TNHH SCHINDLER"), ("nippon", "NIPPON", "NIPPON PAINT"),
                            ("jotun", "JOTUN", "SƠN JOTUN"), ("doan nhat", "ĐOÀN NHẤT", "CƠ ĐIỆN ĐOÀN NHẤT"), ("newsky", "PHƯƠNG TRUNG", "PHƯƠNG TRUNG"), ("nam thuan thanh", "NAM THUẬN THÀNH", "NAM THUẬN THÀNH"),
                            ("mitsubishi electric", "MITSUBISHI ELECTRIC", "MITSUBISHI ELECTRIC"), ("VGC", "VIGLACERA", "VIGLACERA")]:
        sug, txt = ask(q)
        if not sug or first not in sug[0].upper(): F(f"[mở rộng] gợi ý đầu cho “{q}” = {sug[:1]}")
        if legal not in txt.upper(): F(f"[mở rộng] thẻ “{q}” thiếu “{legal}”")
    sug, txt = ask("VGC")  # niêm yết nhưng chưa có BCTC đã kiểm chứng: không hiện doanh thu, không ước lượng
    if "Chưa có số liệu đã kiểm chứng" not in txt or "Doanh thu thuần" in txt or "VGC" not in txt: F("[mở rộng] Viglacera: sai nhãn/hiện số liệu chưa kiểm chứng")
    sug, txt = ask("casta")
    if "cần xác nhận" not in txt.lower(): F("[mở rộng] Casta thiếu cảnh báo tên pháp nhân cần xác nhận")
    sug, txt = ask("thang may", enter=False)
    if len(sug) < 3: F(f"[mở rộng] tìm theo nhóm “thang may” chỉ ra {len(sug)} kết quả")
    t0 = pg.evaluate("() => { const q = document.querySelector('#ncc-q'); const t = performance.now(); q.value = 'schin'; q.dispatchEvent(new Event('input', {bubbles: true})); return performance.now() - t; }")
    if t0 > 200: F(f"[mở rộng] tìm kiếm chậm: {t0:.0f} ms")
    # không tìm thấy
    sug, txt = ask("xyzabc khong ton tai")
    if "chưa có trong dữ liệu" not in txt or "dangkykinhdoanh" not in pg.locator("#ncc-out").inner_html(): F("trạng thái không tìm thấy thiếu thông báo/link tra cứu")
    # bàn phím: ↓ ↓ Enter, Esc
    pg.fill("#ncc-q", "hoa"); pg.wait_for_timeout(250); pg.keyboard.press("ArrowDown"); pg.keyboard.press("ArrowDown"); pg.keyboard.press("Enter"); pg.wait_for_timeout(500)
    if not pg.locator("#ncc-out h3").count() or "chưa có trong dữ liệu" in pg.locator("#ncc-out").inner_text(): F("phím ↓ + Enter không chọn được đơn vị")
    pg.fill("#ncc-q", "hoa"); pg.wait_for_timeout(250); pg.keyboard.press("Escape")
    if pg.locator("#ncc-list").is_visible(): F("Esc không đóng gợi ý")
    # so sánh
    ask("coteccons"); pg.select_option("#ncc-cmp-sel", index=1); pg.wait_for_timeout(400)
    if not pg.locator("#ncc-out .ncc-cmp ~ .tw table").count(): F("so sánh nhanh không hiện bảng")
# ---- Trang chủ: tab "Tra cứu nhà cung cấp" trong box Nhà thầu & chủ đầu tư (#orgseg + #ncc) ----
def home_ncc_checks(pg, w, f, fails):
    def F(m): fails.append((w, f, "ncc-home: " + m))
    n = pg.evaluate("() => [document.querySelectorAll('#ncc').length, document.querySelectorAll('#ncc-q').length, document.querySelectorAll('#ncc-out').length, document.querySelectorAll('#orgseg button[data-k=ncc]').length, document.querySelectorAll('#orgseg button').length]")
    if n != [1, 1, 1, 1, 3]: return F(f"số phần tử [#ncc, #ncc-q, #ncc-out, nút tab, tổng nút] = {n}, cần [1,1,1,1,3]")
    st = pg.evaluate("""() => { const seg = document.getElementById('orgseg'), sr = seg.getBoundingClientRect(), bs = [...seg.querySelectorAll('button')], o = document.getElementById('orgl');
      return {hid: document.getElementById('ncc').hidden, orgl: !o.hidden && o.children.length > 0, clip: seg.scrollWidth > seg.clientWidth + 1 || bs.some(b => b.getBoundingClientRect().right > sr.right + 1 || b.scrollWidth > b.clientWidth + 1),
        lbl: bs.map(b => b.innerText.trim()), aria: seg.querySelector('button[data-k=ncc]').getAttribute('aria-label'),
        lazy: performance.getEntriesByType('resource').filter(r => /supplier-lookup|suppliers\\.json/.test(r.name)).length}; }""")
    if not st["hid"]: F("ô tra cứu không ẩn lúc mới vào (tab mặc định phải là Tin nhà thầu)")
    if not st["orgl"]: F("danh sách tin nhà thầu mặc định trống/ẩn")
    if st["clip"]: F(f"thanh chuyển tab bị cắt/tràn {st['lbl']}")
    if st["lazy"]: F("trang chủ đã tải supplier-lookup/suppliers.json trước khi bấm tab (phải tải lười)")
    if st["aria"] != "Tra cứu nhà cung cấp": F(f"nút tab thiếu aria-label đầy đủ ({st['aria']})")
    if w > 380 and st["lbl"][2] != "Tra cứu nhà cung cấp": F(f"nhãn nút {st['lbl'][2]!r}")
    H = lambda: pg.evaluate("() => { const b = document.getElementById('orgseg').closest('section'); return [Math.round(b.getBoundingClientRect().height * 10) / 10, Math.round(b.parentElement.getBoundingClientRect().height * 10) / 10, document.documentElement.scrollHeight]; }")
    h0 = H(); pg.click("#orgseg button[data-k=ncc]"); pg.wait_for_selector("#ncc:not([hidden]) #ncc-q", timeout=5000); pg.wait_for_timeout(600)
    if pg.evaluate("() => document.getElementById('orgl').hidden") is not True: F("danh sách tin chưa ẩn khi mở tab tra cứu")
    if pg.evaluate("() => document.querySelectorAll('#orgseg button.on').length") != 1: F("không đúng 1 tab đang chọn")
    def ask(q):  # trả về (ms từ lúc gõ đến khi gợi ý hiện + vẽ xong, gợi ý, ms từ Enter đến khi thẻ kết quả vẽ xong, nội dung)
        pg.fill("#ncc-q", ""); pg.wait_for_timeout(100)
        t1 = pg.evaluate("""async (q) => { const i = document.getElementById('ncc-q'), t = performance.now(); i.value = q; i.dispatchEvent(new Event('input', {bubbles: true}));
          await new Promise(r => requestAnimationFrame(() => setTimeout(r, 0))); return performance.now() - t; }""", q)
        sug = pg.locator("#ncc-list li").all_inner_texts()
        t2 = pg.evaluate("""async () => { const i = document.getElementById('ncc-q'), t = performance.now(); i.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
          await new Promise(r => requestAnimationFrame(() => setTimeout(r, 0))); return performance.now() - t; }""")
        return t1, sug, t2, pg.locator("#ncc-out").inner_text()
    for q, first, legal, mst in [("Coteccons", "COTECCONS", "XÂY DỰNG COTECCONS", "0303443233"), ("0303443233", "COTECCONS", "XÂY DỰNG COTECCONS", "0303443233"), ("hoa phat", "HÒA PHÁT", "TẬP ĐOÀN HÒA PHÁT", None), ("CTD", "COTECCONS", "XÂY DỰNG COTECCONS", "0303443233")]:
        t1, sug, t2, txt = ask(q)
        if not sug or first not in sug[0].upper(): F(f"gợi ý đầu cho “{q}” = {sug[:1]}")
        if legal not in txt.upper(): F(f"kết quả “{q}” không có “{legal}”")
        if mst and mst not in txt: F(f"kết quả “{q}” không có MST {mst}")
        if t1 > 200 or t2 > 200: F(f"“{q}”: gợi ý {t1:.0f}ms / kết quả {t2:.0f}ms (cần <200ms)")
        if "chưa tra tự động" not in txt.lower(): F(f"kết quả “{q}” thiếu ghi chú chưa tra tự động")
    t1, sug, t2, txt = ask("Coteccons")
    for k in ("34.340", "788", "0303443233", "CTD", "HOSE", "Theo dõi", "NNT đang hoạt động", "dựa trên Năm tài chính 2026"):
        if k not in txt: F(f"kết quả Coteccons thiếu “{k}”")
    href = pg.evaluate("() => { const a = document.querySelector('#ncc-out a.ncc-full'); return a ? a.getAttribute('href') : null; }")
    if href != "nha-thau.html?ncc=0303443233#ncc": F(f"link hồ sơ đầy đủ = {href}")
    t1, sug, t2, txt = ask("newtecons")
    if "Chưa niêm yết" not in txt or "Chưa có BCTC công khai" not in txt: F("đơn vị chưa niêm yết (Newtecons) không ghi rõ 'Chưa niêm yết' / 'Chưa có BCTC công khai'")
    if "doanh thu" in txt.lower() and "không có doanh thu" not in txt.lower(): F("đơn vị chưa niêm yết hiện doanh thu?")
    t1, sug, t2, txt = ask("xyzabc khong co")
    if "chưa có trong dữ liệu" not in txt or "Tổng cục Thuế" not in txt: F("không có kết quả mà không hướng dẫn tra nguồn chính thức")
    h1 = H()
    if abs(h1[0] - h0[0]) > 1 or abs(h1[1] - h0[1]) > 1 or abs(h1[2] - h0[2]) > 1: F(f"chiều cao box/hàng/trang đổi khi dùng ô tra cứu: trước {h0} sau {h1}")
    ov = pg.evaluate("() => { const b = document.getElementById('ncc'), r = b.getBoundingClientRect(); return {pg: document.documentElement.scrollWidth - innerWidth, inner: b.scrollWidth - b.clientWidth, right: r.right > innerWidth + 1}; }")
    if ov["pg"] > 0 or ov["inner"] > 1 or ov["right"]: F(f"tràn ngang {ov}")
    # bàn phím: ↓ Enter chọn gợi ý thứ 2 → thẻ đổi; Escape đóng danh sách
    pg.fill("#ncc-q", "hoa"); pg.wait_for_timeout(200); pg.keyboard.press("ArrowDown"); pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
    if not pg.locator("#ncc-out .ncc-cmpct").count(): F("chọn bằng bàn phím không ra thẻ")
    # chip thử nhanh
    pg.click("#ncc-quick button[data-id=hoa-binh]"); pg.wait_for_timeout(300)
    if "HÒA BÌNH" not in pg.locator("#ncc-out").inner_text().upper(): F("chip Hòa Bình không ra kết quả")
    # quay lại tab tin: danh sách tin quay lại, ô tra cứu ẩn, box đúng chiều cao ban đầu
    pg.click("#orgseg button[data-k=developer]"); pg.wait_for_timeout(300)
    if not pg.evaluate("() => document.getElementById('ncc').hidden && !document.getElementById('orgl').hidden && document.getElementById('orgl').children.length > 0"): F("quay lại tab tin: trạng thái sai")
    # liên kết hồ sơ đầy đủ mở đúng thẻ ở nha-thau.html
    pg2 = pg.context.new_page()
    try:
        pg2.goto(B + "nha-thau.html?ncc=0303443233", wait_until="networkidle", timeout=60000); pg2.wait_for_timeout(1200)
        if "XÂY DỰNG COTECCONS" not in pg2.locator("#ncc-out").inner_text().upper() or pg2.evaluate("() => document.querySelectorAll('#ncc').length") != 1: F("nha-thau.html?ncc=MST không mở thẻ Coteccons / #ncc không đúng 1 lần")
    finally: pg2.close()

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
                    ov: cards.filter(c => c.getBoundingClientRect().right > W || c.scrollWidth > c.clientWidth + 1).length,
                    imp: cards.filter(c => /Ảnh hưởng đến soạn hợp đồng(?:[/]đấu thầu)?:/.test(c.innerText)).length}; }""")
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
                        _L = [v["label"] for v in _p["clusters"].values()]
                        if len(set(_L)) != len(_L): fails.append((w, f, "policy duplicate cluster labels"))
                        if len({x["cluster"] for x in _H}) != len(_H): fails.append((w, f, "policy home duplicate cluster"))
                        if max([sum(1 for y in _H if y["topics"][0] == x["topics"][0]) for x in _H] or [0]) > 2: fails.append((w, f, "policy home >2 per topic"))
                        if pq["imp"] != sum(1 for x in _H if x.get("impact")): fails.append((w, f, f"policy 'Ảnh hưởng đến soạn hợp đồng' lines {pq['imp']} != home data {sum(1 for x in _H if x.get('impact'))}"))
                        _G = [x for x in _p["items"] if "dia-gioi" in x["topics"]]  # chủ đề Địa giới hành chính (ảnh hưởng soạn hợp đồng)
                        if "dia-gioi" not in _p["topics"]: fails.append((w, f, "policy topic dia-gioi missing"))
                        if any(not x.get("impact") or x["topics"][0] != "dia-gioi" for x in _G): fails.append((w, f, "policy dia-gioi item without impact line / not main topic"))
                        if any(not str(x["url"]).startswith("https://") for x in _G if x.get("seed")): fails.append((w, f, "policy seed bad link"))
                        import datetime as _dt
                        if _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=7))).date() <= _dt.date(2026, 11, 19) and not any(x.get("seed") and "39/2026/QH16" in x["title"] for x in _G): fails.append((w, f, "policy Bắc Ninh seed (NQ 39/2026/QH16) missing"))
                        _P = [x for x in _p["items"] if "ppp" in x["topics"]]  # chủ đề BT / PPP / Đầu tư công (ảnh hưởng soạn hợp đồng/đấu thầu)
                        if "ppp" not in _p["topics"]: fails.append((w, f, "policy topic ppp missing"))
                        if any(not x.get("impact") or x.get("impact_label") != "Ảnh hưởng đến soạn hợp đồng/đấu thầu" for x in _P if x["topics"][0] != "dia-gioi"): fails.append((w, f, "policy ppp item without impact line / label"))
                        if any(not str(x["url"]).startswith("https://") for x in _P if x.get("seed")): fails.append((w, f, "policy ppp seed bad link"))
                        _today = _dt.datetime.now(_dt.timezone(_dt.timedelta(hours=7))).date()
                        for _n, _u, _d in (("377/2026/NĐ-CP", "docid=219746", _dt.date(2026, 11, 30)), ("349/2026/NĐ-CP", "docid=219431", _dt.date(2026, 11, 8))):  # link chính thức có thể nằm trong 'also' khi gộp với tin trùng
                            if _today <= _d and not any(_u in x["url"] or any(_u in a.get("url", "") for a in x.get("also", [])) for x in _P): fails.append((w, f, f"policy ppp official link (NĐ {_n}) missing"))
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
                gq = pg.evaluate("""() => { const b = document.querySelector('#pf-f button[data-k="dia-gioi"]'); if (!b) return {chip: 0}; const want = +(b.querySelector('.mute')?.textContent || 0); b.click();
                  const li = [...document.querySelectorAll('#pf > li:not(.sub)')]; return {chip: 1, want, n: li.length, noimp: li.filter(l => !/Ảnh hưởng đến soạn hợp đồng(?:[/]đấu thầu)?:/.test(l.innerText)).length}; }""")
                if not gq["chip"]: fails.append((w, f, "policy chip 'Địa giới hành chính' missing"))
                elif gq["want"] and (gq["n"] == 0 or gq["noimp"]): fails.append((w, f, f"policy dia-gioi rows {gq['n']}, without impact line {gq['noimp']}"))
                pq2 = pg.evaluate("""() => { const b = document.querySelector('#pf-f button[data-k="ppp"]'); if (!b) return {chip: 0}; const want = +(b.querySelector('.mute')?.textContent || 0); b.click();
                  const li = [...document.querySelectorAll('#pf > li:not(.sub)')]; return {chip: 1, want, n: li.length, noimp: li.filter(l => !/Ảnh hưởng đến soạn hợp đồng(?:[/]đấu thầu)?:/.test(l.innerText)).length}; }""")
                if not pq2["chip"]: fails.append((w, f, "policy chip 'BT / PPP / Đầu tư công' missing"))
                elif pq2["want"] and (pq2["n"] == 0 or pq2["noimp"]): fails.append((w, f, f"policy ppp rows {pq2['n']}, without impact line {pq2['noimp']}"))
            if f == "nha-thau.html" and w in (390, 1366):
                ncc_checks(pg, w, f, fails); pg.wait_for_timeout(300)
            if f == "index.html":
                home_ncc_checks(pg, w, f, fails); pg.wait_for_timeout(300)
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
