#!/usr/bin/env python3
"""Luật & chính sách mới liên quan Masterise (hop-dong.html#chinh-sach + trang chủ).
Real feeds only: Google News RSS (vi) + official/press RSS. Dedup by normalized title, 30-day window.
Each item gets a rule-based score (relevance to Masterise + recency/dynamics) and a one-line reason built ONLY from
matched keywords in the title/summary (no invented facts). Writes trends/data/policy-feed.json. Never raises.
Chủ đề "Địa giới hành chính" (đổi tên/nâng cấp/sáp nhập đơn vị hành chính, địa danh) có thêm dòng "Ảnh hưởng đến soạn hợp đồng" (field impact); tin biên tập có nguồn: trends/seed/policy-seed.json."""
import json, os, re, hashlib, unicodedata, html, datetime as dt, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"); OUT = os.path.join(D, "policy-feed.json")
TZ = dt.timezone(dt.timedelta(hours=7)); KEEP_DAYS = 30
SEED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed", "policy-seed.json"); SEED_DAYS = 60  # tin biên tập (đã đối chiếu nguồn) giữ tới ngày hiệu lực + 60 ngày, dù ngoài cửa sổ 30 ngày
GN = "https://news.google.com/rss/search?q={q}&hl=vi&gl=VN&ceid=VN:vi"
Q = [  # Google News queries (topic hint only; topics are re-derived from text)
 "nghị định Luật Đất đai when:14d", "bảng giá đất Hà Nội TP.HCM when:14d", "thông tư Bộ Xây dựng mới when:14d", "Luật Xây dựng 2025 nghị định hướng dẫn when:14d",
 "Luật Nhà ở chung cư nghị định when:14d", "thời hạn sở hữu chung cư when:30d", "Luật Kinh doanh bất động sản nghị định when:14d", "nhà ở xã hội quy định chủ đầu tư when:14d",
 "giấy phép xây dựng quy định mới when:14d", "phòng cháy chữa cháy chung cư quy định when:14d", "Luật Địa chất và Khoáng sản nghị định when:14d",
 "khai thác cát sỏi vật liệu xây dựng quy định when:14d", "mỏ đá mỏ đất san lấp cấp phép when:14d", "thuế chuyển nhượng bất động sản dự thảo when:14d",
 "dự thảo nghị định bất động sản lấy ý kiến when:14d", "Masterise Homes when:30d",
 "thành lập thành phố trực thuộc trung ương nghị quyết Quốc hội when:30d", "sáp nhập đổi tên tỉnh thành phố đơn vị hành chính when:30d", "sắp xếp đơn vị hành chính cấp xã thành lập phường when:30d",
 "đổi tên địa danh hành chính cập nhật giấy tờ địa chỉ when:30d", "Luật Đầu tư theo phương thức đối tác công tư nghị định hướng dẫn when:30d", "hợp đồng BT thanh toán bằng quỹ đất nghị định when:30d", "nghị định PPP sửa đổi hợp đồng BOT BT when:30d",
 "quyết toán thanh toán dự án BT vướng mắc cơ chế when:30d", "Luật Đầu tư công nghị định hướng dẫn when:30d", "giải ngân vốn đầu tư công Thủ tướng công điện nghị định when:30d",
 "Luật Đấu thầu nghị định lựa chọn nhà thầu when:30d", "lựa chọn nhà đầu tư PPP đấu thầu qua mạng when:30d", "dự án PPP cao tốc đường sắt cơ chế chính sách mới when:30d",
 "site:chinhphu.vn bất động sản OR đất đai OR xây dựng when:14d", "site:thuvienphapluat.vn đất đai OR nhà ở OR xây dựng when:14d",
 "site:moc.gov.vn when:30d", "site:xaydung.gov.vn when:30d", "site:cafeland.vn chính sách when:14d", "site:baochinhphu.vn nhà ở OR đất đai when:14d"]
RSS = [("Chinhphu.vn – Chính sách mới", "https://xaydungchinhsach.chinhphu.vn/chinh-sach-moi.rss"), ("Báo Chính phủ – Chính sách mới", "https://baochinhphu.vn/chinh-sach-moi.rss"),
       ("VnExpress – Pháp luật", "https://vnexpress.net/rss/phap-luat.rss"), ("VnExpress – Bất động sản", "https://vnexpress.net/rss/bat-dong-san.rss")]
PPP_RSS = [("Báo Chính phủ – Kinh tế (lọc BT/PPP/ĐTC)", "https://baochinhphu.vn/kinh-te.rss"), ("Chinhphu.vn – Đầu tư & kinh doanh (lọc BT/PPP/ĐTC)", "https://xaydungchinhsach.chinhphu.vn/dau-tu-kinh-doanh.rss")]  # RSS rộng: chỉ nhận tin chủ đề "ppp"
def strip(s): return unicodedata.normalize("NFD", (s or "").lower().replace("đ", "d")).encode("ascii", "ignore").decode()
# Địa giới / đơn vị hành chính / địa danh: ảnh hưởng trực tiếp tới soạn hợp đồng (địa chỉ các bên, địa điểm dự án, tên cơ quan). Từ khóa đủ cụ thể nên không cần thêm từ "luật/chính sách".
GEO = ["thanh lap thanh pho", "tro thanh thanh pho truc thuoc trung uong", "len thanh pho truc thuoc trung uong", "tinh len thanh pho", "dia gioi hanh chinh", "thay doi dia gioi", "dieu chinh dia gioi",
 "don vi hanh chinh", "sap xep don vi", "sap nhap tinh", "sap nhap xa", "sap nhap phuong", "sap nhap don vi", "doi ten tinh", "doi ten thanh pho", "doi ten phuong", "doi ten xa",
 "thanh lap phuong", "thanh lap cac phuong", "thanh lap xa", "thanh lap cac xa", "xa thanh phuong", "thi tran thanh phuong", "dia danh hanh chinh", "doi ten dia danh", "thay doi dia danh"]
GEO_NEG = ["hanh chinh su nghiep", "xu phat vi pham hanh chinh", "cai cach hanh chinh",  # nhiễu: đơn vị hành chính sự nghiệp…
 "neu co", "co the sap nhap", "khong co ten", "phan dau", "quyet tam", "ban do", "lan truyen", "chua co chu truong", "chua sap xep", "giu nguyen", "khong sap xep", "de an", "ke hoach", "muc tieu", "ung ho", "du kien", "chu truong", "gop y"]  # tin phỏng đoán/định hướng, chưa phải thay đổi có căn cứ
GEO_LEGAL = ["nghi quyet", "thong qua", "hieu luc", "cong bo", "chinh thuc", "ban hanh", "huong dan", "quy dinh", "nghi dinh", "thong tu", "dang ky kinh doanh", "can cuoc", "giay to", "doi giay"]  # tin địa giới phải có dấu hiệu văn bản/hiệu lực/hướng dẫn
# BT / PPP / Đầu tư công / Đấu thầu: văn bản pháp lý & chính sách ảnh hưởng hợp đồng dự án, thanh toán/quyết toán, hồ sơ dự thầu. Chỉ nhận tin có dấu hiệu văn bản/chính sách thật.
PPP_CORE = ["doi tac cong tu", "ppp", "hop dong bt", "du an bt", "hop dong bot", "du an bot", "bot bt", "bt bot", "bot, bt", "bot/bt", "bt/bot", "xay dung chuyen giao", "xay dung - chuyen giao", "thanh toan bang quy dat", "quy dat thanh toan"]
PPP_ICP = ["dau tu cong", "von dau tu cong", "giai ngan von dau tu", "ke hoach dau tu cong", "quyet toan von dau tu", "quyet toan du an hoan thanh", "thanh toan, quyet toan du an"]
PPP_BID = ["luat dau thau", "lua chon nha thau", "lua chon nha dau tu", "he thong mang dau thau quoc gia", "dau thau qua mang"]
PPP_KW = PPP_CORE + PPP_ICP + PPP_BID
PPP_NEG = ["mua thuoc", "goi thau thuoc", "thiet bi y te", "vat tu y te", "hoa chat xet nghiem", "danh muc khu dat",  # nhiễu: đấu thầu thuốc/thiết bị y tế
 "du kien", "kien nghi", "phan dau", "quyet tam", "ung ho", "neu co", "co the", "muc tieu", "tin don"]  # tin phỏng đoán/định hướng
PPP_LEGAL = ["luat dau thau", "luat dau tu", "luat ppp", "luat doi tac cong tu", "luat ngan sach", "nghi dinh", "nghi quyet", "thong tu", "quyet dinh", "cong van", "cong dien", "chi thi", "huong dan", "quy dinh", "hieu luc", "ban hanh", "sua doi", "bo sung", "thong qua", "du thao", "lay y kien", "co che"]
LAWS_PPP = [("luat dau tu theo phuong thuc doi tac cong tu", "Luật PPP"), ("luat ppp", "Luật PPP"), ("luat doi tac cong tu", "Luật PPP"), ("luat dau tu cong", "Luật Đầu tư công")]  # chỉ xét cho tin chủ đề "ppp" (không đổi cụm tin cũ)
def ppp_ok(st): return not any(has(st, n) for n in PPP_NEG) and any(has(st, l) for l in PPP_LEGAL)
# topic -> (label, accent-free keywords). An item must match ≥1 topic AND ≥1 legal/policy word to be kept.
TOPIC = {"dat-dai": ("Đất đai", ["dat dai", "gia dat", "bang gia dat", "quyen su dung dat", "giao dat", "thu hoi dat", "tien su dung dat", "chuyen muc dich su dung dat", "dau gia dat", "so do", "tien thue dat"]),
 "nha-o": ("Nhà ở & chung cư", ["luat nha o", "chung cu", "nha o thuong mai", "nha o xa hoi", "so huu nha", "thoi han so huu", "can ho", "nha chung cu", "cai tao chung cu"]),
 "kd-bds": ("Kinh doanh BĐS", ["kinh doanh bat dong san", "bat dong san", "nha o hinh thanh trong tuong lai", "san giao dich", "chuyen nhuong du an", "ban nha o", "moi gioi"]),
 "xay-dung": ("Xây dựng", ["luat xay dung", "bo xay dung", "giay phep xay dung", "cap phep xay dung", "quy chuan", "tieu chuan xay dung", "quy hoach", "chi phi dau tu xay dung", "hop dong xay dung", "cong trinh xay dung", "dinh muc xay dung"]),
 "pccc": ("PCCC", ["phong chay", "chua chay", "pccc", "cuu nan cuu ho"]),
 "khoang-san": ("Khoáng sản & VLXD", ["khoang san", "cat song", "cat san lap", "cat xay dung", "mo cat", "mo da", "da xay dung", "dat san lap", "mo dat", "set gach", "vat lieu xay dung", "dia chat"]),
 "thue": ("Thuế BĐS", ["thue chuyen nhuong", "thue bat dong san", "thue thu nhap ca nhan tu chuyen nhuong", "thue nha", "thue su dung dat", "thue doi voi nguoi so huu nhieu nha", "le phi truoc ba"]),
 "dia-gioi": ("Địa giới hành chính", GEO),
 "ppp": ("BT / PPP / Đầu tư công", PPP_KW)}
LEGAL = ["luat", "nghi dinh", "thong tu", "nghi quyet", "quyet dinh", "du thao", "quy dinh", "chinh sach", "huong dan", "sua doi", "hieu luc", "ban hanh", "cong van", "chi thi", "bang gia", "cap phep", "lay y kien", "quy chuan"]
# relevance weights (Masterise: luxury condo developer, HN & HCMC) – reason text is fixed per rule
REL = [  # (keywords, points, reason)
 (["masterise", "masteri", "lumiere", "grand marina", "the global city", "masterise homes", "ocean park", "vinhomes smart city masteri"], 45, "Nhắc trực tiếp Masterise / dự án Masterise"),
 (["thoi han so huu", "so huu chung cu", "nien han chung cu"], 22, "Thời hạn sở hữu chung cư – ảnh hưởng sản phẩm căn hộ"),
 (["bang gia dat", "gia dat", "tien su dung dat", "he so dieu chinh gia dat", "tien thue dat"], 22, "Giá đất / tiền sử dụng đất – tác động chi phí quỹ đất & giá bán"),
 (["quyen su dung dat", "giao dat", "cho thue dat", "thu hoi dat", "chuyen muc dich", "dau gia dat", "so do", "giay chung nhan"], 16, "Quyền sử dụng đất / giao đất / cấp sổ – pháp lý dự án"),
 (["chung cu", "can ho", "nha o thuong mai"], 15, "Liên quan chung cư / nhà ở thương mại – sản phẩm chính"),
 (["kinh doanh bat dong san", "hinh thanh trong tuong lai", "chuyen nhuong du an", "mo ban", "dat coc"], 14, "Luật Kinh doanh BĐS – điều kiện mở bán, chuyển nhượng"),
 (["giay phep xay dung", "cap phep xay dung", "tham dinh thiet ke", "luat xay dung", "nghiem thu"], 13, "Cấp phép / thẩm định xây dựng – tiến độ dự án"),
 (["phong chay", "chua chay", "pccc"], 13, "PCCC – điều kiện nghiệm thu, vận hành chung cư"),
 (["cat xay dung", "cat san lap", "cat song", "mo cat", "khai thac cat", "cat soi", "da xay dung", "mo da", "dat san lap", "khoang san", "vat lieu xay dung", "set gach"], 12, "Nguồn cung khoáng sản/VLXD (cát, đá, đất) – giá & tiến độ thi công"),
 (["thue chuyen nhuong", "thue thu nhap ca nhan", "thue su dung dat", "thue tai san", "thue bat dong san", "thue nha", "le phi truoc ba"], 11, "Thuế/phí BĐS – tác động cầu & giá bán"),
 (["nha o xa hoi", "20% quy dat"], 11, "Nghĩa vụ nhà ở xã hội của chủ đầu tư"),
 (["ha noi"], 7, "Áp dụng tại Hà Nội (thị trường dự án)"), (["tp.hcm", "tp hcm", "ho chi minh", "thanh pho ho chi minh", "sai gon"], 7, "Áp dụng tại TP.HCM (thị trường dự án)"),
 (["quy hoach"], 6, "Quy hoạch – ảnh hưởng quỹ đất"), (["hop dong xay dung", "chi phi dau tu xay dung", "dinh muc xay dung", "chi so gia xay dung"], 6, "Quản lý chi phí / HĐ xây dựng"),
 (GEO, 28, "Địa giới/tên đơn vị hành chính thay đổi – ảnh hưởng địa chỉ & địa điểm trong hợp đồng"),
 (PPP_KW, 24, "BT/PPP/đầu tư công/đấu thầu – ảnh hưởng điều kiện hợp đồng dự án, thanh toán & hồ sơ dự thầu")]
DYN = [  # recency/dynamics (max one per group by order)
 (["co hieu luc tu", "hieu luc tu ngay", "chinh thuc co hieu luc", "bat dau co hieu luc", "tu ngay 1/", "tu 1/"], 14, "sắp/đã có hiệu lực"),
 (["ban hanh", "vua ky", "da ky", "thong qua", "chinh thuc"], 12, "văn bản mới ban hành/thông qua"),
 (["du thao", "lay y kien", "gop y"], 10, "dự thảo đang lấy ý kiến"),
 (["sua doi", "bo sung", "thay the", "moi nhat", "quy dinh moi"], 7, "thay đổi quy định"),]
IMPACT = [  # dòng "Ảnh hưởng đến soạn hợp đồng" cho tin địa giới: cố định theo quy tắc (không suy diễn dữ kiện); tin biên tập (seed) có dòng riêng
 (["thanh lap thanh pho", "tro thanh thanh pho", "len thanh pho", "tinh len thanh pho"], "ghi tên đơn vị hành chính mới (thành phố thay cho tỉnh) trong địa chỉ các bên, địa điểm dự án, nơi nhận thông báo/giải quyết tranh chấp từ ngày hiệu lực; xem điều khoản chuyển tiếp của nghị quyết về giấy tờ đã cấp trước đó."),
 (["thanh lap phuong", "thanh lap cac phuong", "thanh lap xa", "thanh lap cac xa", "xa thanh phuong", "thi tran thanh phuong", "doi ten phuong", "doi ten xa"], "ghi đúng cấp và tên xã/phường mới trong địa chỉ pháp nhân, địa điểm dự án, giấy tờ đất/giấy phép; đối chiếu nghị quyết gốc."),
 (["sap nhap", "sap xep don vi", "doi ten tinh", "doi ten thanh pho", "doi ten dia danh", "thay doi dia danh", "dia danh hanh chinh"], "cập nhật tên tỉnh/xã sau sáp nhập – đổi tên trong địa chỉ các bên, địa điểm dự án, hồ sơ pháp lý; ghi tên cũ (nay là …) khi cần đối chiếu giấy tờ cũ."),
 ([], "rà soát địa danh/đơn vị hành chính trong địa chỉ các bên và địa điểm dự án; ghi theo tên và ngày hiệu lực của văn bản gốc.")]
def impact_idx(x):  # 0 = nâng tỉnh lên thành phố, 1 = thành lập phường/xã, 2 = sáp nhập/đổi tên, 3 = chung
    t = strip(x["title"] + " " + x.get("summary", ""))
    return next(i for i, (ks, _) in enumerate(IMPACT) if not ks or any(has(t, k) for k in ks))
IMPACT_PPP = [  # (nhóm từ khóa, câu) – "Ảnh hưởng đến soạn hợp đồng/đấu thầu": gợi ý cố định theo quy tắc, không suy diễn dữ kiện; luôn đối chiếu văn bản gốc
 (PPP_CORE, "đối chiếu căn cứ pháp lý, loại hợp đồng (PPP/BT), điều kiện thanh toán – quyết toán (quỹ đất/ngân sách) và điều khoản chuyển tiếp của văn bản với hợp đồng/dự án đang làm."),
 (PPP_ICP, "kiểm tra nguồn vốn đầu tư công, kế hoạch vốn, điều kiện tạm ứng – thanh toán – quyết toán khi soạn điều khoản thanh toán và hồ sơ dự thầu."),
 (PPP_BID, "cập nhật căn cứ pháp lý, hình thức/quy trình lựa chọn nhà thầu – nhà đầu tư và điều khoản chuyển tiếp trong hồ sơ dự thầu, hợp đồng.")]
def ppp_idx(x):  # 0 = PPP/BT, 1 = đầu tư công, 2 = đấu thầu (ưu tiên theo thứ tự)
    t = strip(x["title"] + " " + x.get("summary", ""))
    return next((i for i, (ks, _) in enumerate(IMPACT_PPP) if any(has(t, k) for k in ks)), 0)
def impact(x):
    tp = x.get("topics") or [""]
    return IMPACT[impact_idx(x)][1] if tp[0] == "dia-gioi" else IMPACT_PPP[ppp_idx(x)][1] if "ppp" in tp else None
def impact_label(x): return "Ảnh hưởng đến soạn hợp đồng/đấu thầu" if (x.get("topics") or [""])[0] != "dia-gioi" and "ppp" in (x.get("topics") or []) else None
DOC = [(r"\bnghi dinh\b|\bnd\s?\d", 8, "Nghị định"), (r"\bthong tu\b", 7, "Thông tư"), (r"\bluat\b", 8, "Luật"), (r"\bnghi quyet\b", 7, "Nghị quyết"), (r"\bquyet dinh\b|\bcong van\b|\bchi thi\b", 4, "QĐ/CV")]
THEME = {1: "Thời hạn sở hữu chung cư", 2: "Giá đất & tiền sử dụng đất", 3: "Quyền sử dụng đất & giao đất", 4: "Chung cư & nhà ở thương mại", 5: "Kinh doanh BĐS (mở bán, chuyển nhượng)",
 6: "Cấp phép & thẩm định xây dựng", 7: "Phòng cháy chữa cháy", 8: "Khoáng sản & VLXD (cát, đá, đất)", 9: "Thuế & phí BĐS", 10: "Nhà ở xã hội", 11: "Hà Nội", 12: "TP.HCM", 13: "Quy hoạch", 14: "Chi phí & HĐ xây dựng", 15: "Nâng tỉnh lên thành phố trực thuộc TW", 16: "Thành lập phường/xã (đổi cấp xã)", 17: "Sáp nhập, sắp xếp & đổi tên đơn vị hành chính",
 18: "PPP & hợp đồng BOT/BT/BOO", 19: "Đầu tư công, giải ngân & quyết toán", 20: "Đấu thầu & lựa chọn nhà thầu/nhà đầu tư"}
THEME_PREF = {"nha-o": [1, 10, 4], "dat-dai": [2, 3, 13], "kd-bds": [5, 10], "xay-dung": [6, 14, 13], "pccc": [7], "khoang-san": [8], "thue": [9], "dia-gioi": [15, 16, 17], "ppp": [18, 19, 20]}  # chủ đề con ưu tiên theo chủ đề chính
GENERIC_LAW = ["luat sua doi", "luat (sua doi)", "luat nay", "luat moi", "luat hoa", "luat chuyen nganh", "luat su", "luat le", "phap luat", "du luat", "luat gop"]
def side_law(t):
    """Dự luật gộp: luật được nhắc ĐẦU TIÊN trong tiêu đề không thuộc nhóm liên quan (vd. 'Luật Quản lý vũ khí…, Luật PCCC') → luật liên quan chỉ là phần phụ."""
    pos = [m.start() for m in re.finditer(r"(?<![a-z])luat ", t) if not any(t.startswith(g, m.start() - (2 if g.startswith("ph") or g.startswith("du") else 0)) for g in GENERIC_LAW)]
    if not pos: return False
    first = pos[0]; return not any(t.startswith(k, first) for k, _ in LAWS) and any(has(t[first:], k) for k, _ in LAWS)
def has(t, k): return re.search(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", t) is not None
def score(x, now):
    t = strip(x["title"] + " " + x.get("summary", "")); rel, why, tags = 0, [], []
    for ks, p, r in REL:
        if ks is GEO and ("dia-gioi" not in x["topics"] or any(has(t, n) for n in GEO_NEG)): continue  # chỉ tính điểm địa giới cho tin thuộc chủ đề này (không đổi điểm tin cũ)
        if ks is PPP_KW and x["topics"][0] != "ppp": continue  # tin cũ có nhãn ppp phụ giữ nguyên điểm
        if any(has(t, k) for k in ks): rel += p; why.append(r)
    side = side_law(strip(x["title"]))
    if side: rel = round(rel * 0.4)  # phạt: lĩnh vực liên quan chỉ là phần phụ của dự luật gộp
    dyn, dn = 0, []
    for ks, p, r in DYN:
        if any(has(t, k) for k in ks): dyn += p; dn.append(r)
    for rx, p, r in DOC:
        if re.search(rx, t): dyn += p; tags.append(r); break
    age = max(0.0, (now - dt.datetime.fromisoformat(x["published"] or x["found"])).total_seconds() / 86400)
    rec = max(0, round(20 * (1 - age / KEEP_DAYS)))  # 20 hôm nay → 0 ở ngày 30
    s = min(100, min(rel, 60) + min(dyn, 25) + rec // 1)
    reason = "; ".join(why[:2]) or "Chính sách ngành BĐS/xây dựng"
    if dn: reason += " · " + ", ".join(dn[:2])
    if side: reason += " · (chỉ là phần phụ của dự luật gộp – giảm điểm)"
    return s, reason, dict(rel=min(rel, 60), dyn=min(dyn, 25), rec=rec)
LAWS = [("luat dat dai", "Luật Đất đai"), ("luat nha o", "Luật Nhà ở"), ("luat kinh doanh bat dong san", "Luật Kinh doanh BĐS"), ("luat xay dung", "Luật Xây dựng"),
 ("luat dia chat va khoang san", "Luật Địa chất & Khoáng sản"), ("luat khoang san", "Luật Địa chất & Khoáng sản"), ("luat quy hoach", "Luật Quy hoạch"), ("luat phong chay", "Luật PCCC"),
 ("luat thue", "Luật Thuế"), ("luat dau thau", "Luật Đấu thầu")]
def cluster(x):
    """Cụm = văn bản gốc (tên luật / số nghị định-thông tư) nếu nhận diện được, nếu không = chủ đề chính. Tin cùng cụm = cùng câu chuyện pháp lý."""
    t = strip(x["title"] + " " + x.get("summary", ""))
    hits = [(t.find(k), lab) for k, lab in (LAWS_PPP + [("luat dau thau", "Luật Đấu thầu")] if x["topics"][0] == "ppp" else LAWS) if has(t, k)]
    hit = [i for i, (ks, _, _) in enumerate(REL) if i > 0 and (ks is not GEO or "dia-gioi" in x["topics"]) and (ks is not PPP_KW or x["topics"][0] == "ppp") and any(has(t, k) for k in ks)]
    th = next((i for i in THEME_PREF.get(x["topics"][0], []) if i in hit), hit[0] if hit else None)  # chủ đề con: ưu tiên luật khớp đúng chủ đề chính
    if x["topics"][0] == "dia-gioi": th = 15 + min(impact_idx(x), 2)  # chủ đề con theo loại thay đổi (mỗi loại ảnh hưởng hợp đồng khác nhau)
    if x["topics"][0] == "ppp": th = 18 + ppp_idx(x)  # chủ đề con: PPP/BT, đầu tư công, đấu thầu
    x["theme"] = f"{x['topics'][0]}:{th}"
    if hits: lab = min(hits)[1]; return "law:" + re.sub(r"[^a-z0-9]+", "-", strip(lab)).strip("-"), lab
    m = re.search(r"(nghi dinh|thong tu|nghi quyet)\s*(?:so\s*)?(\d{1,4}/\d{4}(?:/[a-z\-]+\d{0,2})?)", t)
    if m: lab = {"nghi dinh": "Nghị định", "thong tu": "Thông tư", "nghi quyet": "Nghị quyết"}[m.group(1)] + " " + m.group(2).upper().replace("/ND-", "/NĐ-").replace("/QD-", "/QĐ-"); return "doc:" + re.sub(r"[^a-z0-9]+", "-", lab.lower()), lab
    if th is None: return "topic:" + x["topics"][0], TOPIC[x["topics"][0]][0]
    return f"theme:{x['topics'][0]}:{th}", THEME[th]
SUBJ = {"law:luat-dat-dai": "dat dai", "law:luat-nha-o": "nha o", "law:luat-kinh-doanh-bds": "kinh doanh bat dong san", "law:luat-xay-dung": "xay dung", "law:luat-pccc": "phong chay"}
def pick_home(items, n=6, floor=40, per_topic=2, min_n=5):
    """Trang chủ: tối đa 1 tin/cụm, tối đa 2 tin/chủ đề chính, điểm ≥ floor; thiếu thì bù tới min_n (vẫn 1 tin/cụm)."""
    out, cl, tp = [], set(), {}
    for relax in (False, True):
        for x in items:
            if len(out) >= (n if not relax else min_n): break
            if x["cluster"] in cl or x["theme"] in cl or x in out: continue  # khác văn bản VÀ khác chủ đề con (vd. giá đất)
            t = strip(x["title"])
            if sum(1 for c in cl if c in SUBJ and has(t, SUBJ[c])) >= 2: continue  # bài tổng hợp nhiều luật đã có trên trang chủ
            if not relax and (x["score"] < floor or tp.get(x["topics"][0], 0) >= per_topic): continue
            out.append(x); cl.update((x["cluster"], x["theme"])); tp[x["topics"][0]] = tp.get(x["topics"][0], 0) + 1
    return out
def get(url):
    r = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; MasteriseSCMHub/1.0)"})
    return urllib.request.urlopen(r, timeout=20).read()
def parse(xml, srcname, only=None):
    out = []
    for it in ET.fromstring(xml).iter("item"):
        t = html.unescape((it.findtext("title") or "").strip()); u = (it.findtext("link") or "").strip()
        if not t or not u.startswith("http"): continue
        try: pub = parsedate_to_datetime(it.findtext("pubDate")).astimezone(TZ).isoformat(timespec="minutes")
        except Exception:
            try: pub = dt.datetime.strptime((it.findtext("pubDate") or "").strip(), "%m/%d/%Y %I:%M:%S %p").replace(tzinfo=TZ).isoformat(timespec="minutes")  # chinhphu.vn format (giờ VN)
            except Exception: pub = None
        src = it.find("source"); name = src.text.strip() if src is not None and src.text else srcname
        if src is not None and " - " in t: t = t.rsplit(" - ", 1)[0].strip()
        summ = "" if src is not None else re.sub(r"<[^>]+>|\s+", " ", html.unescape(it.findtext("description") or "")).strip()[:300]
        st = strip(t + " " + summ)
        topics = [k for k, (_, ks) in TOPIC.items() if any(has(st, w) for w in ks) and not (k == "dia-gioi" and (any(has(st, n) for n in GEO_NEG) or not any(has(st, l) for l in GEO_LEGAL))) and not (k == "ppp" and not ppp_ok(st))]
        if only: topics = [k for k in topics if k in only]  # RSS rộng: chỉ giữ chủ đề được chỉ định (không thêm tin cho chủ đề khác)
        if topics == ["ppp"]: pass  # tin chỉ thuộc BT/PPP/ĐTC: chủ đề chính = ppp
        elif "ppp" in topics: topics.remove("ppp"); topics.append("ppp")  # tin đã thuộc chủ đề khác: chỉ gắn nhãn phụ ppp (giữ chủ đề chính, điểm, cụm như cũ)
        if "dia-gioi" in topics: topics.remove("dia-gioi"); topics.insert(0, "dia-gioi")  # tin địa giới: chủ đề chính = địa giới (chip vẫn xếp cuối)
        if not topics or not (topics[0] in ("dia-gioi", "ppp") or any(has(st, w) for w in LEGAL)): continue
        key = re.sub(r"[^a-z0-9]+", " ", strip(t)).strip()
        out.append(dict(id=hashlib.md5(key.encode()).hexdigest()[:12], title=unicodedata.normalize("NFC", t), url=u, source=name, summary=unicodedata.normalize("NFC", summ),
                        topics=topics, published=pub))
    return out
def load_seed(now):
    """Tin biên tập có nguồn cụ thể (seed) – dùng khi nguồn tự động không bắt được. Chỉ giữ khi còn trong hạn (hiệu lực + SEED_DAYS)."""
    out = []
    try: raw = json.load(open(SEED, encoding="utf-8"))["items"]
    except Exception: return out
    for x in raw:
        eff = dt.datetime.fromisoformat(x["effective"]).replace(tzinfo=TZ)
        if now > eff + dt.timedelta(days=SEED_DAYS): continue
        key = re.sub(r"[^a-z0-9]+", " ", strip(x["title"])).strip()
        out.append(dict(id=hashlib.md5(key.encode()).hexdigest()[:12], title=unicodedata.normalize("NFC", x["title"]), url=x["url"], source=x["source"], summary=unicodedata.normalize("NFC", x.get("summary", "")),
                        topics=x.get("topics", ["dia-gioi"]), published=x["published"], found=x["published"], seed=True, effective=x["effective"], impact=x["impact"], **({"impact_label": x["impact_label"]} if x.get("impact_label") else {})))
    return out
def main():
    try: old = json.load(open(OUT, encoding="utf-8"))
    except Exception: old = {}
    items = {x["id"]: x for x in old.get("items", [])}; errors = []; now = dt.datetime.now(TZ); used = {}
    srcs = [(GN.format(q=urllib.parse.quote(q)), "Google News", "Google News: " + q, None) for q in Q] + [(u, n, n, None) for n, u in RSS] + [(u, n, n, ["ppp"]) for n, u in PPP_RSS]
    for url, name, label, only in srcs:
        try:
            got = parse(get(url), name, only); used[label] = len(got)
            for x in got:
                if x["id"] in items:
                    if only: (items[x["id"]]["topics"].append("ppp") if "ppp" not in items[x["id"]]["topics"] else None)  # RSS lọc: chỉ bổ sung nhãn ppp, không đụng chủ đề cũ
                    else: items[x["id"]].update(topics=x["topics"])
                else: items[x["id"]] = {**x, "found": now.isoformat(timespec="minutes")}
        except Exception as e: errors.append(f"{label}: {type(e).__name__}")
    SD = load_seed(now); seeds = {x["id"] for x in SD}
    for x in SD: items[x["id"]] = x  # seed ghi đè bản cũ trong JSON (sửa seed có hiệu lực ngay)
    cut = (now - dt.timedelta(days=KEEP_DAYS)).isoformat(); keep = []
    for x in items.values():
        if x.get("seed"):
            if x["id"] not in seeds: continue  # seed hết hạn / đã gỡ khỏi file seed
        elif (x.get("published") or x.get("found") or "") < cut or (x.get("published") or "") > (now + dt.timedelta(hours=1)).isoformat(): continue
        x["score"], x["why"], x["parts"] = score(x, now)
        if not x.get("seed"):
            x.pop("impact", None); x.pop("impact_label", None); i = impact(x)
            if i: x["impact"] = i
            if impact_label(x): x["impact_label"] = impact_label(x)
        keep.append(x)
    keep.sort(key=lambda x: (-x["score"], -(dt.datetime.fromisoformat(x.get("published") or x["found"]).timestamp())))
    out, seen = [], []  # gộp tin trùng nội dung (cùng sự kiện, khác báo): Jaccard từ tiêu đề ≥ 0,5
    for x in keep:
        w = set(re.sub(r"[^a-z0-9]+", " ", strip(x["title"])).split())
        hit = next((o for o, ws in seen if len(w & ws) / max(1, len(w | ws)) >= 0.5), None)
        if hit is not None: hit.setdefault("also", []).append(dict(source=x["source"], url=x["url"])) if len(hit.get("also", [])) < 4 else None; continue
        x.pop("also", None); seen.append((x, w)); out.append(x)
    keep = out[:400]  # nâng từ 300: thêm chủ đề mới không được đẩy tin cũ điểm thấp ra khỏi danh sách
    for x in keep: x["cluster"], x["cluster_label"] = cluster(x)
    size = {}
    for x in keep: size[x["cluster"]] = size.get(x["cluster"], 0) + 1
    home = [dict(id=x["id"], same=size[x["cluster"]] - 1) for x in pick_home(keep)]
    clusters = {c: dict(label=next(x["cluster_label"] for x in keep if x["cluster"] == c), n=k) for c, k in size.items()}
    labs = {}
    for c, v in clusters.items(): labs.setdefault(v["label"], []).append(c)
    for lab, cs in labs.items():  # tên cụm phải duy nhất: trùng thì thêm chủ đề chính
        if len(cs) > 1:
            for c in cs:
                tp = c.split(":")[1] if c.count(":") >= 1 and c.split(":")[1] in TOPIC else None
                th = int(c.split(":")[2]) if c.startswith("theme:") else None
                home_tp = next((k for k, v in THEME_PREF.items() if th in v), None)  # chủ đề "tự nhiên" của chủ đề con giữ tên gốc
                if tp and not c.startswith("law:") and tp != home_tp: clusters[c]["label"] = f"{lab} · {TOPIC[tp][0]}"
    assert len({v["label"] for v in clusters.values()}) == len(clusters), "duplicate cluster labels"
    for x in keep: x["cluster_label"] = clusters[x["cluster"]]["label"]
    json.dump(dict(schema_version=1, updated=now.isoformat(timespec="minutes"), window_days=KEEP_DAYS, topics={k: v[0] for k, v in TOPIC.items()},
                   note="Tin tự động từ RSS/Google News – CHƯA biên tập. Điểm & lý do sinh theo quy tắc từ khóa trong tiêu đề/tóm tắt; luôn đọc văn bản gốc.",
                   scoring="Điểm = Liên quan Masterise (≤60) + Tính mới/động lực văn bản (≤25: hiệu lực, ban hành, dự thảo, sửa đổi, loại văn bản) + Độ mới (≤20, giảm tuyến tính 30 ngày); tối đa 100.",
                   home=home, clusters=clusters, home_rule="Trang chủ: tối đa 1 tin/cụm văn bản và 1 tin/chủ đề con, 2 tin/chủ đề chính, điểm ≥ 40 (thiếu thì bù tới 5).",
                   sources=used, errors=errors, count=len(keep), items=keep), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"policy feed: {len(keep)} items, {len(errors)} errors")
if __name__ == "__main__": main()
