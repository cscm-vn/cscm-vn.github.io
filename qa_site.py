"""Site-wide audit + regression: python qa_site.py BASE_URL [--shots]
Asserts each shared component mounts exactly once per page, no console/page errors,
no horizontal overflow, no broken internal links, no mojibake in Vietnamese text."""
import sys, re, glob, os, json, time, urllib.request, urllib.parse
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
    # đơn vị thêm theo yêu cầu anh Hà (4 tên nêu riêng + đợt mở rộng): tìm được, đúng pháp nhân/MST; chưa niêm yết -> 'Chưa có BCTC công khai'; cờ tên pháp nhân cho đơn vị chưa chắc
    for q, first, legal in [("fountech", "FOUNTECH", "CỔ PHẦN FOUNTECH"), ("kingsteel", "KINGSTEEL", "KINGSTEEL VIỆT NAM"), ("an phat cuong", "AN PHÁT CƯỜNG", "CỔ PHẦN AN PHÁT CƯỜNG"),
                            ("long giang", "LONG GIANG", "ĐÔ THỊ LONG GIANG"), ("0105647362", "KINGSTEEL", "KINGSTEEL VIỆT NAM"), ("acefic", "ACEFIC", "ACE THÁI BÌNH DƯƠNG"), ("wilo", "WILO", "WILO VIỆT NAM"),
                            ("nem", "NEM", "NỘI THẤT NEM"), ("dong ngo", "ĐÔNG NGÔ", "TẬP ĐOÀN ĐÔNG NGÔ"), ("bm windows", "BM WINDOWS", "BM WINDOWS"), ("mau nghe thuat", "MÀU NGHỆ THUẬT", "MÀU NGHỆ THUẬT"),
                            ("tinh phu qui", "TÍNH PHÚ QUÍ", "TÍNH PHÚ QUÍ"), ("catinat", "CATINAT", "CATINAT DESIGN"), ("gg derco", "GG DECOR", "GG DECOR")]:
        sug, txt = ask(q)
        if not sug or first not in sug[0].upper(): F(f"[đơn vị mới] gợi ý đầu cho “{q}” = {sug[:1]}")
        if legal not in txt.upper(): F(f"[đơn vị mới] thẻ “{q}” thiếu “{legal}”")
        if "Chưa có BCTC công khai" not in txt and "LGL" not in txt: F(f"[đơn vị mới] thẻ “{q}” thiếu nhãn 'Chưa có BCTC công khai'")
        if "Doanh thu thuần" in txt: F(f"[đơn vị mới] thẻ “{q}” không được hiện doanh thu")
    for q in ("long giang", "catinat", "gg decor", "bkt"):
        sug, txt = ask(q)
        if "cần xác nhận" not in txt.lower(): F(f"[đơn vị mới] thẻ “{q}” thiếu cảnh báo tên pháp nhân cần xác nhận")
    sug, txt = ask("long giang")  # niêm yết (LGL) nhưng chưa có số liệu đã kiểm chứng: không hiện số
    if "LGL" not in txt or "Chưa có số liệu đã kiểm chứng" not in txt or "Doanh thu thuần" in txt: F("[đơn vị mới] Long Giang (LGL): sai nhãn/hiện số liệu chưa kiểm chứng")
    for q in ("fountech", "kingsteel", "an phat cuong"):
        sug, txt = ask(q)
        if "cần xác nhận" in txt.lower(): F(f"[đơn vị mới] thẻ “{q}” không nên có cờ tên pháp nhân (đã khai pháp nhân trong orgs.json)")
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
# ---- Trang chủ: box Nhà thầu & chủ đầu tư – số tin lấp đủ chỗ trống, không tràn, không đổi chiều cao hàng ----
def home_news_checks(pg, w, f, fails):
    def F(m): fails.append((w, f, "orgbox: " + m))
    J = """() => { const ul = document.getElementById('orgl'), sec = ul.closest('section'), row = sec.parentElement, sib = [...row.children].find(z => z !== sec), sb = sec.getBoundingClientRect(), ub = ul.getBoundingClientRect();
      const two = getComputedStyle(row).gridTemplateColumns.trim().split(/\\s+/).length > 1, sibNat = Math.max(...[...sib.children].map(c => c.getBoundingClientRect().bottom)) - sb.top, ids = [...ul.querySelectorAll('li a')].map(a => a.href);
      return {n: ul.querySelectorAll('li').length, two, row: row.getBoundingClientRect().height, sibNat, ulBot: ub.bottom - sb.top, box: sb.height, gap: sb.bottom - ub.bottom, dup: ids.length - new Set(ids).size, ov: ul.scrollWidth - ul.clientWidth, empty: !!ul.querySelector('li.mute')}; }"""
    for k in ("contractor", "developer", "contractor"):
        pg.click(f'#orgseg button[data-k={k}]'); pg.wait_for_timeout(300); r = pg.evaluate(J)
        if r["empty"]: F(f"{k}: danh sách tin trống"); continue
        if r["dup"]: F(f"{k}: tin trùng link x{r['dup']}")
        if r["ov"] > 1: F(f"{k}: danh sách tràn ngang {r['ov']}px")
        if r["two"]:
            if r["ulBot"] > r["sibNat"] + 1: F(f"{k}: danh sách ({r['ulBot']:.0f}px) vượt đáy cột bên cạnh ({r['sibNat']:.0f}px) – sẽ làm cao hàng")
            if abs(r["row"] - r["box"]) > 1 or r["row"] > r["sibNat"] + 2: F(f"{k}: chiều cao hàng {r['row']:.0f} ≠ chiều cao cột bên cạnh {r['sibNat']:.0f}")
            if r["gap"] > 110: F(f"{k}: còn trống {r['gap']:.0f}px dưới danh sách (n={r['n']})")
            if r["n"] < 12: F(f"{k}: chỉ {r['n']} tin ở 2 cột (cần ≥12 khi đủ dữ liệu)")
        elif r["n"] != 8: F(f"{k}: 1 cột phải 8 tin, thực tế {r['n']}")
    pg.click('#orgseg button[data-k=contractor]'); pg.wait_for_timeout(200)

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

# ---- Hợp đồng: khối "Xác thực thư bảo lãnh" (#bao-lanh): bảng tra cứu ngân hàng + sổ bảo lãnh (localStorage) ----
BL_BANKS = {"Vietcombank": "https://www.vietcombank.com.vn/vi-VN/To-chuc/SMEs/SME---Kiem-tra-bao-lanh", "BIDV": "https://bidv.com.vn/vn/dinh-che-tai-chinh/cong-cu-tien-ich/tra-thu-bao-lanh",
  "Techcombank": "https://tracuubaolanh.techcombank.com.vn/", "VietinBank": "https://ebanking.vietinbank.vn/tracuubaolanh/lcVerifyGet", "MB": "https://www.mbbank.com.vn/Form/documents",
  "Eximbank": "https://eximbank.com.vn/tra-cuu-bao-lanh", "NCB": "https://www.ncb-bank.vn/mdonline/", "TPBank": "https://xacthucbaolanh.tpb.vn/xacthucbaolanh/", "HDBank": "https://hdbank.com.vn/vi/corporate/cong-cu/guarantee"}
BL_NOLINK = ["ACB", "SHB", "Agribank", "VPBank"]
BL_EX = ["https://baoquangninh.vn/canh-bao-thu-doan-lam-gia-chung-thu-bao-lanh-ngan-hang-post2317160.html", "https://baodauthau.vn/lam-gia-tai-lieu-ngan-hang-khi-du-thau-hau-qua-lon-can-xu-nghiem-post115293.html"]
BL_BOT_BLOCKED = {"https://www.ncb-bank.vn/mdonline/"}  # NCB trả 403 cho trình duyệt tự động/curl (đã mở được bằng trình duyệt thật khi xác minh) → chỉ kiểm đúng địa chỉ, không HEAD
def bl_link_ok(u):
    for _ in range(3):  # máy chủ một số ngân hàng chập chờn → thử lại tối đa 3 lần
        try:
            if urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "vi"}), timeout=25).status < 400: return True
        except Exception: pass
    return False
def bao_lanh_checks(pg, w, f, fails):
    def F(m): fails.append((w, f, "bao-lanh: " + m))
    st = pg.evaluate("""() => { const s = document.querySelectorAll('#bao-lanh'), el = s[0]; if (!el) return {n: 0};
      const rows = [...el.querySelectorAll('#bl-banks tbody tr[data-bank]')];
      return {n: s.length, book: el.querySelectorAll('#bl-book').length, tbl: el.querySelectorAll('#bl-tbl').length, prev: el.previousElementSibling?.id, next: el.nextElementSibling?.id,
        banks: rows.map(r => [r.dataset.bank, r.querySelector('a.bl-btn')?.getAttribute('href') || null, r.querySelector('a.bl-btn')?.getAttribute('rel') || '', r.querySelector('a.bl-btn')?.target || '', r.innerText]),
        ex: [...el.querySelectorAll('.bl-ex a')].map(a => a.getAttribute('href')), txt: el.innerText,
        ov: el.scrollWidth - el.clientWidth, ovp: document.documentElement.scrollWidth - innerWidth}; }""")
    if st["n"] != 1: return F(f"khối xuất hiện {st['n']} lần")
    if st["prev"] != "tranh-chap" or st["next"] != "checklist": F(f"sai vị trí (trước {st['prev']}, sau {st['next']})")
    if st["book"] != 1 or st["tbl"] != 1: F("thiếu sổ bảo lãnh")
    got = {b[0]: b[1] for b in st["banks"] if b[1]}
    if got != BL_BANKS: F(f"danh sách link ngân hàng sai: {set(got.items()) ^ set(BL_BANKS.items())}")
    for b in st["banks"]:
        if b[1] and (b[3] != "_blank" or "noopener" not in b[2]): F(f"link {b[0]} thiếu target/rel")
        if not b[1] and "Cần xin văn bản xác thực" not in b[4]: F(f"{b[0]} không có link phải ghi 'Cần xin văn bản xác thực'")
    if [b[0] for b in st["banks"] if not b[1]] != BL_NOLINK: F("danh sách ngân hàng không có link khác dự kiến")
    if st["ex"] != BL_EX: F(f"link ví dụ vụ việc sai {st['ex']}")
    for k in ("không tự kiểm tra", "không xác nhận thật/giả thay ngân hàng", "chỉ nằm trên trình duyệt của máy này", "không gửi dữ liệu đi đâu", "Xuất CSV", "captcha"):
        if k not in st["txt"]: F(f"thiếu câu “{k}”")
    if st["ov"] > 1: F(f"khối tràn ngang {st['ov']}px")
    if w == W[0]:
        for u in BL_EX + list(BL_BANKS.values()):
            if u in BL_BOT_BLOCKED: continue
            if not bl_link_ok(u): F("link hỏng " + u)
    # --- sổ bảo lãnh: ngày giả lập 31/12/2026 (giờ VN), context riêng để không ảnh hưởng trang khác ---
    br = pg.context.browser; ctx = br.new_context(viewport={"width": w, "height": 900}); ctx.route("**/gc.zgo.at/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
    errs = []
    try:
        ctx.clock.install(time="2026-12-31T12:00:00+07:00"); p2 = ctx.new_page()
        p2.on("console", lambda m: m.type == "error" and errs.append(m.text)); p2.on("pageerror", lambda e: errs.append(str(e)))
        p2.goto(pg.url.split("#")[0], wait_until="networkidle", timeout=90000); p2.wait_for_timeout(1500)
        p2.evaluate("() => localStorage.removeItem('hopdong-baolanh-v1')"); p2.reload(wait_until="networkidle"); p2.wait_for_timeout(800)
        if p2.locator("#bl-body tr[data-id]").count() != 0 or "Chưa có thư bảo lãnh" not in p2.locator("#bl-body").inner_text(): F("sổ rỗng không hiện dòng trống")
        def add(no, bank, ct, ty, amt, exp, ver="0", vd="", vby=""):
            p2.click("#bl-add"); fm = "#bl-form "
            p2.fill(fm + "[name=no]", no); p2.fill(fm + "[name=bank]", bank); p2.fill(fm + "[name=contractor]", ct); p2.select_option(fm + "[name=type]", ty); p2.fill(fm + "[name=amount]", amt); p2.fill(fm + "[name=expiry]", exp)
            p2.select_option(fm + "[name=verified]", ver); p2.fill(fm + "[name=vdate]", vd); p2.fill(fm + "[name=vby]", vby); p2.click("#bl-save"); p2.wait_for_timeout(120)
        p2.click("#bl-add")  # lưu rỗng → báo lỗi, không thêm dòng
        p2.fill("#bl-form [name=no]", ""); p2.evaluate("() => { const f = document.getElementById('bl-form'); f.noValidate = true; }"); p2.click("#bl-save")
        if not p2.locator("#bl-err").inner_text().strip() or p2.locator("#bl-body tr[data-id]").count() != 0: F("lưu form rỗng không báo lỗi/đã thêm dòng")
        p2.click("#bl-cancel")
        if not p2.locator("#bl-form").is_hidden(): F("Hủy không đóng form")
        D = [("T-1", "2026-12-30", "over"), ("T0", "2026-12-31", "d7"), ("T7", "2027-01-07", "d7"), ("T8", "2027-01-08", "d15"), ("T15", "2027-01-15", "d15"), ("T16", "2027-01-16", "d30"), ("T30", "2027-01-30", "d30"), ("T31", "2027-01-31", "ok")]
        for i, (no, exp, lv) in enumerate(D): add("BL-" + no, "Vietcombank", "Nhà thầu " + no, ["Tạm ứng", "Thực hiện HĐ", "Dự thầu", "Bảo hành"][i % 4], "2.200.000.000", exp, "1" if i == 0 else "0", "2026-12-20" if i == 0 else "", "Hà" if i == 0 else "")
        got = p2.evaluate("() => [...document.querySelectorAll('#bl-body tr[data-id]')].map(r => [r.cells[0].textContent, r.dataset.lvl, r.cells[6].textContent, getComputedStyle(r.cells[0]).backgroundColor, r.cells[4].textContent, r.cells[7].textContent])")
        if len(got) != 8: return F(f"thêm 8 dòng nhưng có {len(got)}")
        for (no, exp, lv), g in zip(D, got):
            if g[0] != "BL-" + no or g[1] != lv: F(f"mốc màu {no}: {g[1]} (cần {lv})")
        bg = {g[1]: g[3] for g in got}
        if len(set(bg.values())) != 5 or bg["ok"] not in ("rgba(0, 0, 0, 0)", "rgb(255, 255, 255)"): F(f"màu nền các mốc không phân biệt: {bg}")
        if got[0][2] != "Quá hạn 1 ngày" or got[1][2] != "Hết hạn hôm nay" or got[2][2] != "Còn 7 ngày": F(f"chữ 'còn lại' sai {[g[2] for g in got[:3]]}")
        if got[0][4] != "2.200.000.000": F(f"định dạng giá trị {got[0][4]}")
        if not got[0][5].startswith("Đã xác thực 20/12/2026") or "Hà" not in got[0][5]: F(f"trạng thái xác thực {got[0][5]}")
        # sửa
        p2.locator("#bl-body tr[data-lvl=ok] button", has_text="Sửa").click(); p2.fill("#bl-form [name=contractor]", "Nhà thầu SỬA"); p2.fill("#bl-form [name=expiry]", "2027-01-20"); p2.click("#bl-save"); p2.wait_for_timeout(120)
        row = p2.locator("#bl-body tr", has_text="BL-T31")
        if row.count() != 1 or "Nhà thầu SỬA" not in row.inner_text() or row.get_attribute("data-lvl") != "d30": F("sửa dòng không đúng (tên/mốc màu)")
        if p2.locator("#bl-body tr[data-id]").count() != 8: F("sửa làm đổi số dòng")
        # xóa (2 bước)
        row.locator("button", has_text="Xóa").click()
        if p2.locator("#bl-body tr[data-id]").count() != 8: F("bấm Xóa lần 1 đã xóa luôn")
        p2.locator("#bl-body tr", has_text="BL-T31").locator("button", has_text="Không").click()
        p2.locator("#bl-body tr", has_text="BL-T31").locator("button", has_text="Xóa").click(); p2.locator("#bl-body tr", has_text="BL-T31").locator("button", has_text="Xóa thật?").click(); p2.wait_for_timeout(120)
        if p2.locator("#bl-body tr[data-id]").count() != 7 or p2.locator("#bl-body tr", has_text="BL-T31").count(): F("xóa dòng không hoạt động")
        # chống chèn HTML + CSV an toàn công thức
        add("<img src=x onerror=window.__bl=1>", "TPBank", "=HYPERLINK(\"http://x\")", "Dự thầu", "1500000", "2027-06-30")
        if p2.evaluate("() => !!window.__bl || document.querySelectorAll('#bl-body img').length") : F("dữ liệu nhập bị diễn giải thành HTML")
        if "<img src=x" not in p2.locator("#bl-body").inner_text(): F("không hiện nguyên văn dữ liệu nhập")
        # tải lại: dữ liệu còn
        p2.reload(wait_until="networkidle"); p2.wait_for_timeout(800)
        if p2.locator("#bl-body tr[data-id]").count() != 8: F(f"tải lại còn {p2.locator('#bl-body tr[data-id]').count()} dòng (cần 8)")
        # CSV
        with p2.expect_download(timeout=15000) as dl: p2.click("#bl-csv")
        d = dl.value; raw = open(d.path(), "rb").read()
        if not d.suggested_filename.startswith("so-bao-lanh-20261231") or not d.suggested_filename.endswith(".csv"): F(f"tên file CSV {d.suggested_filename}")
        if not raw.startswith(b"\xef\xbb\xbf"): F("CSV thiếu BOM UTF-8")
        import csv as _csv, io as _io
        rows = list(_csv.reader(_io.StringIO(raw.decode("utf-8-sig"))))
        if rows[0][:6] != ["Số thư", "Ngân hàng", "Nhà thầu", "Loại", "Giá trị (VND)", "Ngày hết hạn"] or len(rows) != 9: F(f"CSV header/số dòng sai ({len(rows)})")
        else:
            if rows[1][0] != "BL-T-1" or rows[1][5] != "2026-12-30" or rows[1][4] != "2200000000" or rows[1][6] != "-1" or rows[1][7] != "Đã xác thực" or rows[1][8] != "2026-12-20" or rows[1][9] != "Hà": F(f"CSV dòng 1 sai {rows[1]}")
            if not any(r[2].startswith("'=HYPERLINK") for r in rows[1:]): F("CSV không vô hiệu hóa công thức (=...)")
            if not any(r[0].startswith("<img") for r in rows[1:]): F("CSV mất dữ liệu có ký tự đặc biệt")
        if errs: F("console: " + " | ".join(errs[:3]))
        p2.evaluate("() => localStorage.removeItem('hopdong-baolanh-v1')")
    except Exception as e: F(f"lỗi kiểm thử {type(e).__name__}: {str(e)[:200]}")
    finally: ctx.close()

# ---------- PWA (manifest, icon, service worker, installability) ----------
def _get(u, t=30):
    r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=t); return r.status, r.headers.get("Content-Type", ""), r.read()
def _png_size(b):
    import struct
    return struct.unpack(">II", b[16:24]) if b[:8] == b"\x89PNG\r\n\x1a\n" else None
def nc_checks(pg, w, f, fails):
    """Tin nhân công: nút taxonomy, tin biên tập có hàm ý + nguồn, bộ lọc 'Nhân công' ở thi-truong, danh mục hiện tin, không lỗi console."""
    def F(m): fails.append((w, f, "nhan-cong: " + m))
    if f == "thi-truong.html":
        opts = pg.evaluate("() => [...document.querySelectorAll('select option')].map(o => o.textContent.trim())")
        if "Nhân công" not in opts: F(f"bộ lọc chủ đề thiếu 'Nhân công': {opts}")
        return
    if f != "danh-muc.html": return
    p2 = pg.context.new_page(); errs = []
    p2.on("console", lambda m: m.type == "error" and errs.append(m.text)); p2.on("pageerror", lambda e: errs.append(str(e)))
    try:
        p2.goto(B + "danh-muc.html?c=tt.nhan-cong&tab=news", wait_until="networkidle", timeout=90000); p2.wait_for_timeout(800)
        h1 = p2.evaluate("() => (document.querySelector('h1')||{}).textContent || ''")
        if "Nhân công" not in h1: F(f"tiêu đề danh mục sai: {h1!r}")
        rows = p2.evaluate("() => [...document.querySelectorAll('li, .news li, #news li')].filter(l => l.querySelector('a[href^=http]') && l.offsetParent).map(l => [l.innerText.trim(), l.querySelector('a[href^=http]').href])")
        if len(rows) < 12: F(f"tab Tin chỉ có {len(rows)} dòng (<12)")
        if sum("Biên tập" in r[0] for r in rows) < 12: F("thiếu nhãn 'Biên tập' cho các tin biên tập")
        ov = p2.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")
        if ov > 0: F(f"overflow {ov}px")
        tax = p2.evaluate("async () => (await HUB.tax()).byId['tt.nhan-cong']"); 
        if not tax: F("taxonomy thiếu tt.nhan-cong")
        errs = [e for e in errs if "zgo.at" not in e and "goatcounter" not in e.lower()]
        if errs: F("console: " + " | ".join(errs[:3]))
    finally: p2.close()
def pwa_head_checks(pg, w, f, fails):
    h = pg.evaluate("""() => { const q = s => [...document.head.querySelectorAll(s)];
      return {man: q('link[rel=manifest]').map(l => l.href), apple: q('link[rel=apple-touch-icon]').map(l => [l.href, l.sizes.value]),
        theme: q('meta[name=theme-color]').map(m => m.content), cap: q('meta[name=apple-mobile-web-app-capable]').map(m => m.content),
        mcap: q('meta[name=mobile-web-app-capable]').map(m => m.content), title: q('meta[name=apple-mobile-web-app-title]').map(m => m.content),
        reg: q('script').filter(s => s.textContent.includes('serviceWorker.register')).length}; }""")
    if h["man"] != [B + "manifest.webmanifest"]: fails.append((w, f, f"link manifest sai/thiếu/trùng: {h['man']}"))
    if len(h["apple"]) != 1 or h["apple"][0][1] != "180x180": fails.append((w, f, f"apple-touch-icon sai/thiếu/trùng: {h['apple']}"))
    if h["theme"] != ["#0e1a2b"]: fails.append((w, f, f"theme-color {h['theme']}"))
    if h["cap"] != ["yes"] or h["mcap"] != ["yes"] or h["title"] != ["SCM Hub"]: fails.append((w, f, f"meta app-capable/title {h['cap']} {h['mcap']} {h['title']}"))
    if h["reg"] != 1: fails.append((w, f, f"script đăng ký service worker x{h['reg']}"))
def pwa_checks(br, fails):
    F = lambda m: fails.append(("-", "PWA", m))
    try:
        st, ct, body = _get(B + "manifest.webmanifest")
        if st != 200: return F(f"manifest HTTP {st}")
        m = json.loads(body)
    except Exception as e: return F(f"manifest không tải/parse được: {e}")
    exp = dict(name="Masterise Construction SCM Hub", short_name="SCM Hub", lang="vi", start_url="./", scope="/", display="standalone", theme_color="#0e1a2b", background_color="#f5f6f8")
    for k, v in exp.items():
        if m.get(k) != v: F(f"manifest.{k} = {m.get(k)!r} (cần {v!r})")
    if "json" not in ct and "manifest" not in ct and "octet" not in ct: F(f"manifest Content-Type lạ: {ct}")
    got = set()
    for ic in m.get("icons", []):
        try:
            st, ct2, b = _get(urllib.parse.urljoin(B + "manifest.webmanifest", ic["src"]))
            sz = _png_size(b); want = tuple(int(x) for x in ic["sizes"].split("x"))
            if st != 200 or sz != want: F(f"icon {ic['src']}: HTTP {st}, kích thước {sz} (khai {want})")
            got.add((want[0], ic.get("purpose", "any")))
        except Exception as e: F(f"icon {ic.get('src')}: {e}")
    for need in ((192, "any"), (512, "any"), (512, "maskable")):
        if need not in got: F(f"manifest thiếu icon {need}")
    try:
        _, _, b = _get(B + "scm-apple-touch-180.png")
        if _png_size(b) != (180, 180): F("apple-touch-icon không phải PNG 180x180")
    except Exception as e: F(f"apple-touch-icon: {e}")
    try:
        st, ct, b = _get(B + "sw.js"); t = b.decode()
        if st != 200 or "javascript" not in ct: F(f"sw.js HTTP {st} {ct}")
        if "__SW_VERSION__" in t or not re.search(r'const VERSION = "[0-9a-f]{10}"', t): F("sw.js chưa được đóng dấu phiên bản")
    except Exception as e: F(f"sw.js: {e}")
    # đăng ký + hành vi thật của service worker (context cho phép SW, chặn goatcounter)
    ctx = br.new_context(viewport={"width": 390, "height": 800}, service_workers="allow")
    ctx.route("**/gc.zgo.at/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=""))
    errs = []
    try:
        pg = ctx.new_page(); pg.on("console", lambda x: x.type == "error" and errs.append(x.text)); pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(B + "index.html", wait_until="networkidle", timeout=90000)
        ready = pg.evaluate("""async () => { const r = await Promise.race([navigator.serviceWorker.ready, new Promise(s => setTimeout(() => s(null), 15000))]); return r ? {scope: r.scope, active: !!r.active} : null; }""")
        if not ready or not ready["active"]: return F("service worker không kích hoạt")
        if ready["scope"] != B: F(f"scope SW {ready['scope']} != {B}")
        pg.reload(wait_until="networkidle"); pg.wait_for_timeout(1500)
        if not pg.evaluate("() => !!navigator.serviceWorker.controller"): F("trang chưa được SW kiểm soát sau khi tải lại")
        # installability (CDP): không còn lỗi
        cdp = ctx.new_cdp_session(pg); pg.wait_for_timeout(1500)
        ie = cdp.send("Page.getInstallabilityErrors").get("installabilityErrors", [])
        if ie: F(f"installability errors: {[e.get('errorId') for e in ie]}")
        am = cdp.send("Page.getAppManifest"); mj = json.loads(am.get("data") or "{}")
        if am.get("errors") or mj.get("display") != "standalone": F(f"CDP manifest lỗi: {am.get('errors')}")
        # cache: có HTML/JSON/css/js, không có /api, không có khác nguồn, không có ?query
        keys = pg.evaluate("""async () => { const out = []; for (const k of await caches.keys()) for (const r of await (await caches.open(k)).keys()) out.push(r.url); return out; }""")
        if not any(u.endswith("/hub.css") for u in keys): F("cache không có hub.css")
        bad = [u for u in keys if "/api/" in u or not u.startswith(B) or "?" in u]
        if bad: F(f"cache chứa mục không được phép: {bad[:3]}")
        # dữ liệu luôn lấy mạng trước: khi mạng có thì thấy ngay nội dung mới (giả lập bản deploy mới đổi hub.json)
        pg.evaluate("() => fetch('data/hub.json', {cache: 'no-cache'}).then(r => r.text())")  # chắc chắn đã có bản lưu
        fresh = {"v": "MOI-" + str(int(time.time()))}
        def serve_new(route): route.fulfill(status=200, content_type="application/json", body=json.dumps(fresh))
        ctx.route("**/data/hub.json", serve_new)
        got_json = pg.evaluate("() => fetch('data/hub.json', {cache: 'no-cache'}).then(r => r.text())")
        if json.loads(got_json) != fresh: F("SW phục vụ dữ liệu cũ khi có mạng (mạng trước không hoạt động)")
        ctx.unroute("**/data/hub.json", serve_new)
        pg.evaluate("() => fetch('data/hub.json', {cache: 'no-cache'}).then(r => r.text())")  # nạp lại bản thật vào cache (tránh bản giả lập làm hỏng bước offline)
        # offline cơ bản: trang đã xem vẫn mở được, dữ liệu đã lưu vẫn đọc được
        ctx.set_offline(True)
        pg.reload(wait_until="domcontentloaded"); pg.wait_for_timeout(1500)
        if pg.locator(".hn-bar").count() != 1: F("offline: không mở lại được trang đã xem")
        ok = pg.evaluate("() => fetch('data/hub.json').then(r => r.ok).catch(() => false)")
        if not ok: F("offline: không đọc được dữ liệu đã lưu")
        ctx.set_offline(False)
    except Exception as e: F(f"lỗi khi kiểm tra SW: {e}")
    finally:
        errs = [e for e in errs if "zgo.at" not in e and "goatcounter" not in e.lower() and "ERR_INTERNET_DISCONNECTED" not in e and "Failed to load resource" not in e]
        if errs: F("console: " + " | ".join(errs[:3]))
        ctx.close()


# ---------- cột "Xu hướng" ở bảng giá danh-muc.html ----------
XH_JS = """async () => {
  const t = await HUB.tax(), h = await HUB.get("hub.json"); const ids = (HUB.qs("c") && t.byId[HUB.qs("c")]) ? (t.byId[HUB.qs("c")].level === 1 ? t.byId[HUB.qs("c")].children.map(x => x.id) : [HUB.qs("c")]) : [];
  const P = h.items.filter(x => ids.includes(x.tax)); const hist = {};
  await Promise.all(P.map(async x => { try { const j = await (await fetch("history/" + x.id + ".json", {cache: "no-store"})).json(); hist[x.id] = (j.points || []).filter(p => p.price != null).sort((a, b) => a.date.localeCompare(b.date)).map(p => [p.date, p.price]); } catch (e) { hist[x.id] = null; } }));
  const rows = [...document.querySelectorAll("#pt tbody tr:not(.mtg-h)")];
  return {th: [...document.querySelectorAll("#pt thead th")].map(x => x.textContent.trim()), nP: P.length, nRows: rows.length,
    pend: rows.filter(r => r.querySelector("td.xh")?.textContent.trim() === "…").length,
    noCell: rows.filter(r => !r.querySelector("td.xh")).length,
    rows: rows.map(r => { const td = r.querySelector("td.xh"), a = td && td.querySelector("a"), id = new URLSearchParams((r.querySelector("td a") || {href: ""}).href.split("?")[1] || "").get("id");
      const poly = td && td.querySelector("polyline"); return {id, hist: hist[id], txt: td ? td.textContent.trim() : null, href: a ? a.getAttribute("href") : null, poly: poly ? poly.getAttribute("points").split(" ").length : 0,
        cls: td && td.querySelector(".xt") ? td.querySelector(".xt").className : "", own: td ? td.scrollWidth - td.clientWidth : 0}; }),
    ov: document.documentElement.scrollWidth - innerWidth};
}"""
def xh_group_check(pg, w, label, fails):
    F = lambda m: fails.append((w, label, "xu hướng: " + m))
    try: pg.wait_for_selector("#pt tbody tr:not(.mtg-h)", timeout=15000)
    except Exception: return None  # nhóm không có bảng giá → bỏ qua
    pg.wait_for_function("() => ![...document.querySelectorAll('#pt td.xh')].some(td => td.textContent.trim() === '…')", timeout=20000); pg.wait_for_timeout(300)
    r = pg.evaluate(XH_JS)
    if r["th"][-1] != "Xu hướng": F(f"tiêu đề cột cuối {r['th'][-1:]}")
    if r["nRows"] != r["nP"]: F(f"số dòng {r['nRows']} != số mã {r['nP']}")
    if r["noCell"]: F(f"{r['noCell']} dòng thiếu ô Xu hướng")
    if r["pend"]: F(f"{r['pend']} ô còn '…' (không tải được trk.json)")
    if r["ov"] > 0: F(f"trang tràn ngang {r['ov']}px")
    vis = pg.evaluate("""() => { const r = [...document.querySelectorAll('#pt tbody tr:not(.mtg-h)')].slice(0, 5), vw = innerWidth <= 600;
      return r.map(x => { const a = vw ? x.querySelector('.xhm') : x.querySelector('td.xh'), cs = a && getComputedStyle(a); return [!!a && cs.display !== 'none' && a.getBoundingClientRect().width > 0, a ? a.textContent.trim() : null, x.querySelector('td.xh') ? x.querySelector('td.xh').textContent.trim() : null]; }); }""")
    for v in vis:
        if not v[0]: F("xu hướng không hiển thị trên màn hình này")
        if v[1] != v[2]: F(f"bản hiển thị trên điện thoại '{v[1]}' != cột '{v[2]}'")
    for x in r["rows"]:
        hp = x["hist"]; n = len(hp) if hp is not None else None
        if hp is None: F(f"{x['id']}: không đọc được history json"); continue
        if x["href"] != "mat-hang.html?id=" + x["id"] and n >= 2: F(f"{x['id']}: link {x['href']}")
        if n < 2:
            if x["txt"] != "mới thu" or x["poly"]: F(f"{x['id']}: {n} điểm nhưng hiện {x['txt']!r}/poly={x['poly']}")
            continue
        if x["poly"] != min(n, 60): F(f"{x['id']}: sparkline {x['poly']} điểm != history {min(n, 60)}")
        d0 = hp[0][0]; want = d0[8:10] + "/" + d0[5:7]; chg = (hp[-1][1] / hp[0][1] - 1) * 100
        m = re.match(r"^([+−])(\d+,\d+)% từ (\d\d/\d\d)$", x["txt"] or "")
        if not m: F(f"{x['id']}: định dạng '{x['txt']}'"); continue
        if m.group(3) != want: F(f"{x['id']}: ngày đầu {m.group(3)} != {want}")
        val = float(m.group(2).replace(",", ".")) * (-1 if m.group(1) == "−" else 1)
        if abs(val - chg) > 0.06: F(f"{x['id']}: % {val} != {chg:.2f} (tính từ history)")
        if (chg > 0.0) != ("up" in x["cls"].split()) and abs(chg) >= 0.05: F(f"{x['id']}: màu {x['cls']} không khớp dấu {chg:.2f}")
    return r
def xh_checks(pg, w, f, fails, groups=True):
    if f != "danh-muc.html": return
    p2 = pg.context.new_page(); errs = []
    p2.on("console", lambda m: m.type == "error" and errs.append(m.text)); p2.on("pageerror", lambda e: errs.append(str(e)))
    try:
        base = B + "danh-muc.html"
        p2.goto(base + "?c=xd.be-tong&tab=gia", wait_until="networkidle", timeout=90000)
        ids = p2.evaluate("async () => (await HUB.tax()).tree.map(x => x.id)") if groups else ["xd.be-tong"]
        done = 0
        for gid in ids:
            p2.goto(base + "?c=" + gid + "&tab=gia", wait_until="networkidle", timeout=90000)
            if xh_group_check(p2, w, "danh-muc.html?c=" + gid, fails) is not None: done += 1
        if groups and done < 2: fails.append((w, f, f"cột Xu hướng: chỉ kiểm được {done} nhóm có bảng giá"))
        # bấm một sparkline → mở đúng mat-hang.html của mã đó
        p2.goto(base + "?c=xd.be-tong&tab=gia", wait_until="networkidle", timeout=90000)
        p2.wait_for_function("() => document.querySelector('#pt td.xh a')", timeout=20000)
        href = p2.evaluate("() => document.querySelector('#pt td.xh a').getAttribute('href')")
        p2.locator("#pt .xhm a" if w <= 600 else "#pt td.xh a").first.click(); p2.wait_for_url(re.compile(r"mat-hang\.html\?id="), timeout=20000); p2.wait_for_timeout(1200)
        if not p2.url.endswith(href): fails.append((w, f, f"bấm sparkline mở {p2.url} (cần …{href})"))
    except Exception as e: fails.append((w, f, f"xu hướng: lỗi khi kiểm tra: {str(e)[:150]}"))
    finally:
        errs = [e for e in errs if "zgo.at" not in e and "goatcounter" not in e.lower()]
        if errs: fails.append((w, f, "xu hướng: console " + " | ".join(errs[:3])))
        p2.close()
def ai_page_checks(pg, w, f, fails):
    """huong-dan.html: mục 'Dùng dữ liệu hub với AI' có link llms.txt/prices.csv/hub.sqlite + đoạn mẫu; không tràn ngang."""
    if f != "huong-dan.html": return
    r = pg.evaluate("""() => { const h = document.querySelector('#dung-voi-ai'); if (!h) return null; const c = h.nextElementSibling;
      return {links: [...c.querySelectorAll('a')].map(a => a.getAttribute('href')), code: (c.querySelector('code')||{}).textContent || '', vis: !!h.offsetParent, ov: document.documentElement.scrollWidth - document.documentElement.clientWidth}; }""")
    if not r: return fails.append((w, f, "ai: thiếu mục #dung-voi-ai"))
    for need in ("llms.txt", "prices.csv", "hub.sqlite"):
        if need not in r["links"]: fails.append((w, f, f"ai: mục AI thiếu link {need}"))
    if "https://cscm-vn.github.io/llms.txt" not in r["code"]: fails.append((w, f, "ai: thiếu đoạn mẫu để dán"))
    if not r["vis"] or r["ov"] > 0: fails.append((w, f, f"ai: mục AI không hiện/tràn ngang {r['ov']}px"))
def ai_checks(br, fails):
    """Dữ liệu cho AI: file tồn tại + 200 + kích thước; prices.csv & hub.sqlite khớp hub.json (mọi mã); mọi link trong llms.txt/sitemap sống; SQL mẫu chạy được; SW không cache chúng."""
    import sqlite3, csv as _csv, io as _io, tempfile, random
    F = lambda m: fails.append(("-", "AI-data", m))
    root = B.rstrip("/")
    got = {}
    for name, maxb in (("llms.txt", 200_000), ("prices.csv", 2_000_000), ("hub.sqlite", 25_000_000), ("robots.txt", 5_000), ("sitemap.xml", 200_000)):
        try:
            st, ct, b = _get(B + name)
            if st != 200 or not b: F(f"{name}: HTTP {st}, {len(b or b'')} byte"); continue
            if len(b) > maxb: F(f"{name}: {len(b)} byte > {maxb}")
            got[name] = b
        except Exception as e: F(f"{name}: {e}")
    if len(got) < 5: return
    llms = got["llms.txt"].decode("utf-8"); first = llms.split("\n", 1)[0]
    if not re.match(r"generated_at: 20\d\d-\d\d-\d\dT\d\d:\d\d\+07:00", first): F(f"llms.txt dòng đầu không có generated_at: {first[:60]}")
    for k in ("Chưa có BCTC công khai", "Tên pháp nhân cần xác nhận", "12±2", "trung vị", "mới thu", "VAT"):
        if k not in llms: F(f"llms.txt thiếu nội dung quy ước: {k}")
    if "??" in llms or "{EX}" in llms: F("llms.txt còn chỗ chưa điền (?? hoặc {EX})")
    if "\ufffd" in llms or re.search(r"[ÃÂ][\x80-\xbf]|â€", llms): F("llms.txt lỗi mã hoá UTF-8")
    hub = json.loads(urllib.request.urlopen(B + "data/hub.json", timeout=60).read()); H = {x["id"]: x for x in hub["items"]}
    csvb = got["prices.csv"]
    if csvb[:3] == b"\xef\xbb\xbf": F("prices.csv có BOM (cột đầu bị sai tên khi đọc bằng pandas)")
    rows = list(_csv.DictReader(_io.StringIO(csvb.decode("utf-8"))))
    if list(rows[0].keys())[0] != "generated_at": F("prices.csv: cột đầu phải là generated_at")
    if len(rows) != len(H) or {r["item_id"] for r in rows} != set(H): F(f"prices.csv {len(rows)} dòng khác hub.json {len(H)} mã")
    def eqn(a, b, tol=1e-9):
        if a in ("", None): return b is None
        if b is None: return False
        return abs(float(a) - float(b)) <= tol * max(1, abs(float(b)))
    bad = 0
    for r in rows:
        x = H.get(r["item_id"]);
        if not x: continue
        for col, k in (("price", "price"), ("price_high", "price_high"), ("vnd", "vnd"), ("d1_pct", "d1"), ("w1_pct", "w1"), ("mom_pct", "mom"), ("yoy_pct", "yoy"), ("s0_pct", "s0"), ("n_hist", "n_hist")):
            if not eqn(r[col], x.get(k)): bad += 1; bad < 4 and F(f"prices.csv {r['item_id']}.{col}={r[col]} ≠ hub.json {x.get(k)}")
        for col, k in (("as_of", "as_of"), ("unit", "unit"), ("first_date", "first_date")):
            if (r[col] or None) != x.get(k): bad += 1; bad < 4 and F(f"prices.csv {r['item_id']}.{col}={r[col]} ≠ hub.json {x.get(k)}")
        if r["is_new"] != ("1" if (x.get("n_hist") or 0) < 2 else "0"): F(f"prices.csv {r['item_id']}.is_new sai")
        if r["mat_hang_url"] != f"https://cscm-vn.github.io/mat-hang.html?id={r['item_id']}": F(f"prices.csv {r['item_id']}.mat_hang_url sai")
    if bad: F(f"prices.csv lệch hub.json {bad} ô")
    if not any("Bê tông" in r["name"] for r in rows): F("prices.csv: tiếng Việt lỗi (không thấy 'Bê tông')")
    tf = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False); tf.write(got["hub.sqlite"]); tf.close()
    try:
        db = sqlite3.connect(tf.name); meta = dict(db.execute("select key, value from meta"))
        for k in ("generated_at", "build_commit", "hub_built", "schema_version"):
            if not meta.get(k): F(f"hub.sqlite meta thiếu {k}")
        if meta.get("generated_at") != first.split()[1]: F(f"generated_at lệch: sqlite {meta.get('generated_at')} vs llms.txt {first.split()[1]}")
        if rows[0]["generated_at"] != meta.get("generated_at"): F("generated_at prices.csv ≠ hub.sqlite")
        for t in ("taxonomy", "items", "prices_latest", "price_history", "compare_hn_hcm", "compare_parts", "suppliers", "supplier_fin", "news"):
            n = db.execute(f"select count(*) from {t}").fetchone()[0]
            if n == 0: F(f"hub.sqlite bảng {t} rỗng")
            if str(n) != meta.get(f"rows.{t}"): F(f"hub.sqlite meta rows.{t}={meta.get(f'rows.{t}')} ≠ {n}")
            cols = [c[1] for c in db.execute(f"pragma table_info({t})")]
            for c in cols:
                if f"- {c} (" not in llms: F(f"llms.txt không mô tả cột {t}.{c}")
        if db.execute("select count(*) from items").fetchone()[0] != len(H): F("hub.sqlite items ≠ hub.json")
        for iid in random.sample(sorted(H), min(30, len(H))):
            x = H[iid]; q = db.execute("select price, price_high, as_of, d1_pct, s0_pct, n_hist, first_date from prices_latest where item_id=?", (iid,)).fetchone()
            if not q or not (eqn(q[0], x["price"]) and eqn(q[1], x.get("price_high")) and q[2] == x["as_of"] and eqn(q[3], x.get("d1")) and eqn(q[4], x.get("s0")) and q[5] == x["n_hist"] and q[6] == x.get("first_date")): F(f"hub.sqlite prices_latest {iid} lệch hub.json")
            n = db.execute("select count(*) from price_history where item_id=?", (iid,)).fetchone()[0]
            h = json.loads(urllib.request.urlopen(B + f"history/{iid}.json", timeout=30).read())["points"]
            if n != len([p for p in h if p.get("price") is not None]): F(f"hub.sqlite price_history {iid}: {n} ≠ history json {len(h)}")
        for c in hub["compare"]:
            q = db.execute("select hn, hcm, diff_pct from compare_hn_hcm where label=?", (c["label"],)).fetchone()
            if not q or q[0] != c["hn"] or q[1] != c["hcm"] or q[2] != c["diff_pct"]: F(f"hub.sqlite compare {c['label']} lệch hub.json")
        sup = json.loads(urllib.request.urlopen(B + "data/suppliers.json", timeout=30).read())["units"]
        if db.execute("select count(*) from suppliers").fetchone()[0] != len(sup): F("hub.sqlite suppliers ≠ suppliers.json")
        if db.execute("select count(*) from suppliers where has_fin=1").fetchone()[0] != sum(1 for u in sup if u.get("fin")): F("hub.sqlite has_fin ≠ suppliers.json")
        nconf = sum(1 for u in sup if any(f.get("t") == "Tên pháp nhân cần xác nhận" for f in (u.get("flags") or [])))
        if db.execute("select count(*) from suppliers where name_needs_confirm=1").fetchone()[0] < nconf: F("hub.sqlite name_needs_confirm ít hơn suppliers.json")
        if db.execute("select count(*) from suppliers where has_fin=0 and exists(select 1 from supplier_fin where supplier_id=suppliers.id)").fetchone()[0]: F("nhà cung cấp has_fin=0 mà có số BCTC")
        mk = json.loads(urllib.request.urlopen(B + "data/market.json", timeout=30).read())["items"]
        if db.execute("select count(*) from news where kind='market'").fetchone()[0] != len(mk): F("hub.sqlite news(market) ≠ market.json")
        for i, q in enumerate(re.findall(r"```sql\n(.*?)\n```", llms, re.S), 1):
            for st in [re.sub(r"--.*", "", x).strip() for x in q.split(";")]:
                if st:
                    try:
                        if not db.execute(st).fetchall(): F(f"SQL mẫu #{i} không trả dòng nào")
                    except Exception as e: F(f"SQL mẫu #{i} lỗi: {e}")
        db.close()
    finally: os.unlink(tf.name)
    urls = set(re.findall(r"https://cscm-vn\.github\.io/[^\s)>\]\"'`,;]*[^\s)>\]\"'`,;.]", llms)) | set(re.findall(r"<loc>([^<]+)</loc>", got["sitemap.xml"].decode()))
    urls = {u.replace("https://cscm-vn.github.io", root) for u in urls if "<" not in u and ">" not in u}
    if len(urls) < 30: F(f"llms.txt+sitemap chỉ có {len(urls)} URL")
    for u in sorted(urls):
        if not link_ok(u): F(f"link chết trong llms.txt/sitemap: {u}")
    rb = got["robots.txt"].decode()
    if "Sitemap:" not in rb or re.search(r"^Disallow:\s*/\s*$", rb, re.M): F("robots.txt chặn đọc hoặc thiếu Sitemap")
    # service worker không được cache các file này
    try:
        ctx = br.new_context(); pg = ctx.new_page(); ctx.route("**/gc.zgo.at/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body="")); ctx.route("**/*.goatcounter.com/**", lambda r: r.fulfill(status=200, content_type="application/json", body="{}"))
        pg.goto(B + "index.html", wait_until="networkidle", timeout=90000); pg.wait_for_timeout(2500)
        r = pg.evaluate("""async () => { await navigator.serviceWorker.ready; for (const u of ['llms.txt', 'prices.csv', 'hub.sqlite', 'sitemap.xml']) await fetch(u + '?x=' + Date.now()).then(r => r.arrayBuffer());
          const keys = []; for (const c of await caches.keys()) for (const q of await (await caches.open(c)).keys()) keys.push(new URL(q.url).pathname); return keys; }""")
        for k in r:
            if re.search(r"(llms\.txt|prices\.csv|hub\.sqlite|sitemap\.xml)$", k): F(f"service worker đã cache {k}")
        ctx.close()
    except Exception as e: F(f"kiểm SW cache lỗi: {e}")
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
            if f == "hop-dong.html":
                bao_lanh_checks(pg, w, f, fails); pg.wait_for_timeout(300)
            if f == "index.html":
                home_news_checks(pg, w, f, fails); home_ncc_checks(pg, w, f, fails); pg.wait_for_timeout(300)
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
            pwa_head_checks(pg, w, f, fails)
            xh_checks(pg, w, f, fails, groups=(w in (390, 1366)))
            nc_checks(pg, w, f, fails)
            ai_page_checks(pg, w, f, fails)
            pg.close()
        ctx.close()
    pwa_checks(br, fails)
    ai_checks(br, fails)
    br.close()
try:  # sanity: cùng thành phố & cùng cơ sở, mác cao hơn không được rẻ hơn mác thấp hơn
    import json as _j
    _h = _j.load(urllib.request.urlopen(B + "data/hub.json", timeout=30))
    _r = sorted([(int(re.search(r"M(\d+)", c["label"]).group(1)), c) for c in _h.get("compare", []) if c.get("basis") == "rmc" and re.search(r"M\d+", c["label"])], key=lambda t: t[0])
    for (g1, c1), (g2, c2) in zip(_r, _r[1:]):
        for reg in ("hn", "hcm"):
            if c2[reg] < c1[reg]: fails.append(("-", "hub.json", f"grade order {reg}: M{g2} {c2[reg]} < M{g1} {c1[reg]}"))
except Exception as e: fails.append(("-", "hub.json", f"grade-order check error: {e}"))
try:  # tin nhân công trong market.json: mỗi tin có hàm ý mua sắm/đấu thầu, nguồn https, ngày hợp lệ, không trùng URL
    _m = [x for x in _j.load(urllib.request.urlopen(B + "data/market.json", timeout=30))["items"] if "tt.nhan-cong" in x.get("tax", [])]
    if len(_m) < 12: fails.append(("-", "market.json", f"tin nhân công {len(_m)} < 12"))
    _seen = set()
    for x in _m:
        if not x.get("takeaway") or "đấu thầu" not in x["takeaway"] and "mua sắm" not in x["takeaway"].lower(): fails.append(("-", "market.json", "thiếu hàm ý mua sắm/đấu thầu: " + x["title"][:50]))
        if not x.get("sources") or not all(s["url"].startswith("https://") for s in x["sources"]): fails.append(("-", "market.json", "nguồn không https: " + x["title"][:50]))
        if not re.match(r"20\d\d-\d\d-\d\d$", x.get("date", "")): fails.append(("-", "market.json", "ngày sai: " + x["title"][:50]))
        for s_ in x.get("sources", []):
            if s_["url"] in _seen: fails.append(("-", "market.json", "trùng nguồn " + s_["url"][:60]))
            _seen.add(s_["url"])
except Exception as e: fails.append(("-", "market.json", f"nhan-cong check error: {e}"))
try:  # bộ lọc feeds.py: dương tính = tin nhân công xây dựng, âm tính = nhiễu (xây dựng Đảng, nhà máy, nông nghiệp...)
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "trends")); import feeds as _fd
    for _t, _e in [("Giá nhân công xây dựng chạm mức 1 triệu đồng/công", 1), ("Thiếu hụt nhân lực ngành xây dựng: cần bắt tay ba nhà", 1), ("Công trường khát thợ, nhà thầu phải đổi cách giữ người", 1),
                   ("Thiếu thợ xây, phụ hồ: doanh nghiệp trả lương tới hơn 20 triệu", 1), ("Xây dựng Đảng trong sạch vững mạnh, nâng cao tiền công nhân", 0), ("Nhà máy Samsung thiếu lao động, tăng lương cho công nhân", 0),
                   ("Giá nhân công nông nghiệp tăng mùa thu hoạch", 0), ("Phù hợp với điều kiện thực tế, bất động sản phân hóa", 0), ("Doanh nghiệp thu phí không dừng chưa làm rõ bản chất", 0)]:
        if _fd.is_labor(_fd.strip(_t)) != bool(_e): fails.append(("-", "feeds.py", f"is_labor sai ({_e}): {_t}"))
except Exception as e: fails.append(("-", "feeds.py", f"is_labor check error: {e}"))
print(f"pages={len(PAGES)} widths={W} links_checked={len(checked)}")
for x in fails: print("FAIL", *x)
print("ALL OK" if not fails else f"{len(fails)} failures"); sys.exit(1 if fails else 0)
