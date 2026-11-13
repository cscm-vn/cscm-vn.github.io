# Tóm tắt tuần thương hiệu (13/11/2026, lần chạy đầu – phủ 30 ngày 14/10–13/11/2026): trends/data/brands.json
# (A) digest cho hãng/danh mục; (B) upsert emerging[]. Mọi số liệu lấy từ bài đã mở; giả định đàm phán ghi "GIẢ ĐỊNH".
import json, unicodedata
from datetime import date, timedelta
N = lambda s: unicodedata.normalize("NFC", s)
TODAY = "2026-11-13"
p = "trends/data/brands.json"; d = json.load(open(p, encoding="utf-8"))
d["updated"] = TODAY
nz = lambda o: N(o) if isinstance(o, str) else ({k: nz(v) for k, v in o.items()} if isinstance(o, dict) else ([nz(x) for x in o] if isinstance(o, list) else o))
S = lambda name, url, dt: {"name": name, "url": url, "date": dt}
def dg(text, impl, sources):
    return nz({"date": TODAY, "text": text, "impl": impl, "sources": sorted(sources, key=lambda s: s["date"], reverse=True)})

# ---------- Nguồn
s_bmp1 = S("CafeF 18/10/2026 – Nhựa Bình Minh gãy chuỗi tăng trưởng lợi nhuận", "https://cafef.vn/nhua-binh-minh-gay-chuoi-tang-truong-loi-nhuan-lien-tuc-188261018082526136.chn", "2026-10-18")
s_bmp2 = S("Tạp chí Kinh tế – Tài chính 26/10/2026 – BMP cắt 126 tỷ đồng hỗ trợ đại lý", "https://tapchikinhtetaichinh.vn/nhua-binh-minh-cat-126-ty-dong-ho-tro-dai-ly-170643.html", "2026-10-26")
s_ntp = S("Tạp chí Công Thương 23/10/2026 – Nhựa Tiền Phong lợi nhuận 9 tháng vượt 37% kế hoạch", "https://tapchicongthuong.vn/nhua-tien-phong--loi-nhuan-9-thang-vuot-37--ke-hoach-nam-560316.htm", "2026-10-23")
s_vgc = S("Báo Pháp luật – Doanh nhân 25/10/2026 – Viglacera lãi quý III gấp 5,2 lần", "https://doanhnhan.baophapluat.vn/viglacera-vgc-lai-quy-iii-tang-gap-5-2-lan-mang-kinh-va-guong-chuyen-tu-lo-sang-lai.html", "2026-10-25")
s_acg = S("Báo Pháp luật – Doanh nhân 30/10/2026 – Gỗ An Cường lãi 424,72 tỷ đồng 9 tháng", "https://doanhnhan.baophapluat.vn/go-an-cuong-acg-lai-424-72-ty-dong-trong-9-thang-tai-san-do-dang-tang-hon-44-lan.html", "2026-10-30")
s_dulux = S("VIR 06/10/2026 – AkzoNobel bán mảng Dulux ĐNA cho Nippon Paint 1,35 tỷ USD", "https://vir.com.vn/akzonobel-to-sell-dulux-business-for-135-billion-162193.html", "2026-10-06")
s_jotun = S("Báo Gia Lai 30/10/2026 – Khởi tố vụ buôn bán sơn, bột trét giả nhãn hiệu Jotun", "https://baogialai.com.vn/gia-lai-khoi-to-vu-an-buon-ban-son-bot-tret-gia-nhan-hieu-jotun-post603457.html", "2026-10-30")
s_cadisun = S("VietnamPlus 10/10/2026 – Sai phạm kế toán tại Cadisun: PTGĐ kháng cáo", "https://www.vietnamplus.vn/sai-pham-ke-toan-tai-cadisun-pho-tong-giam-doc-khang-cao-xin-giam-nhe-hinh-phat-post1141198.amp", "2026-10-10")
s_taya = S("VnBusiness 26/10/2026 – Cáp điện Taya: dòng tiền kinh doanh âm, nợ vay tăng", "https://vnbusiness.vn/cap-dien-taya-tya-dong-tien-kinh-doanh-am-gan-290-ty-dong-no-vay-tang-manh.html", "2026-10-26")
s_tcr = S("Báo Pháp luật – Doanh nhân 16/10/2026 – Taicera lãi quý 3, lỗ lũy kế vẫn ăn mòn vốn", "https://doanhnhan.baophapluat.vn/gom-su-taicera-tcr-bat-ngo-bao-lai-quy-3-nho-hoan-nhap-du-phong-lo-luy-ke-van-an-mon-von.html", "2026-10-16")
s_inax = S("Eva.vn 12/11/2026 – INAX 30 năm tại VN: Spalet Clean và Flash Sale", "https://eva.vn/tieu-dung/inax-ky-niem-30-nam-tai-viet-nam-gioi-thieu-dong-san-pham-spalet-clean-va-chuong-trinh-flash-sale-toan-quoc-c2a688799.html", "2026-11-12")
s_hettich = S("VnExpress 17/10/2026 – Hettich Việt Nam đưa phụ kiện nội thất Đức vào dự án nhà ở", "https://vnexpress.net/hettich-viet-nam-dua-phu-kien-noi-that-duc-vao-cac-du-an-nha-o-5132595.html", "2026-10-17")
s_schindler = S("CafeF 13/10/2026 – Schindler 30 năm tại VN, giải pháp thang máy thế hệ mới", "https://cafef.vn/schindler-ky-niem-30-nam-tai-viet-nam-gioi-thieu-loat-giai-phap-thang-may-the-he-moi-188261013173325884.chn", "2026-10-13")
s_samsung = S("VnExpress 28/10/2026 – Chủ tịch Samsung VN: đô thị hóa, AI 'mở khóa' ngành HVAC", "https://vnexpress.net/chu-tich-samsung-viet-nam-do-thi-hoa-ai-mo-khoa-nganh-hvac-5137933.html", "2026-10-28")
s_sanyo = S("Thanh Niên 26/10/2026 – Panasonic VN ra mắt điều hòa SANYO Comfort Series", "https://thanhnien.vn/panasonic-viet-nam-ra-mat-dong-dieu-hoa-comfort-series-cua-thuong-hieu-sanyo-185261026105527447.htm", "2026-10-26")
s_taihan = S("CafeF 09/11/2026 – Taihan đặt nhà máy cáp siêu cao áp 1.400 tỷ đồng tại Đồng Nai", "https://cafef.vn/vuot-trung-quoc-va-an-do-viet-nam-thuyet-phuc-thanh-cong-ong-lon-han-quoc-dat-nha-may-dau-tien-rong-bang-8-san-bong-da-von-1400-ty-dong-188261108213441966.chn", "2026-11-09")
s_alco = S("VnEconomy 07/11/2026 – Nhôm Việt Dũng khánh thành nhà máy thứ 3", "https://vneconomy.vn/nhom-viet-dung-khanh-thanh-nha-may-thu-3-quy-mo-hon-100000m2.htm", "2026-11-07")
s_jomoo1 = S("Báo Đầu tư 03/11/2026 – JOMOO gia nhập thị trường Nhật Bản", "https://baodautu.vn/jomoo-gia-nhap-thi-truong-nhat-ban-d736279.html", "2026-11-03")
s_jomoo2 = S("VietnamPlus 02/11/2026 – JOMOO, thương hiệu dẫn đầu doanh số bồn cầu thông minh", "https://www.vietnamplus.vn/jomoo-thuong-hieu-dan-dau-the-gioi-ve-doanh-so-bon-cau-thong-minh-khang-dinh-vi-the-khi-gia-nhap-thi-truong-nhat-ban-post1145727.vnp", "2026-11-02")
s_uu1 = S("Dân trí 12/10/2026 – Dấu ấn nội thất từ các công trình biểu tượng tại showroom Uuviet Hà Nội", "https://dantri.com.vn/bat-dong-san/dau-an-noi-that-tu-cac-cong-trinh-bieu-tuong-tai-showroom-uuviet-solutions-ha-noi-20261012104630690.htm", "2026-10-12")
s_uu2 = S("VnEconomy 11/10/2026 – Showroom Uuviet Solutions Hà Nội", "https://vneconomy.vn/showroom-uuviet-solutions-ha-noi-diem-giao-thoa-giua-noi-that-au-my-va-chuan-song-ha-thanh.htm", "2026-10-11")
s_fotile = S("Báo Mới (Tri thức – Znews) 08/09/2026 – Fotile Việt Nam kiến tạo gian bếp thông minh", "https://baomoi.com/fotile-viet-nam-kien-tao-gian-bep-thong-minh-cho-gia-dinh-hien-dai-c56001146.epi", "2026-09-08")

# ---------- (A) Digest hãng
B = {
 "binh-minh": dg("Quý III/2026 BMP có doanh thu thuần 1.463 tỷ đồng (-4,5%), LNST 319,3 tỷ đồng (-8,9%); giá vốn tăng 9,4% do hạt PVC đắt, biên gộp giảm từ 47,9% xuống 40,3%. Hãng bù bằng cách cắt khoảng 126 tỷ đồng hỗ trợ đại lý (còn ~108 tỷ so với 234 tỷ cùng kỳ) – giá ống không tăng theo được chi phí vì cạnh tranh.",
     "Chiết khấu qua kênh đại lý đang bị thu hẹp → giá mua thực tế qua đại lý có thể nhích lên; nên chào giá dự án trực tiếp với hãng và đặt BMP cạnh Tiền Phong để giữ đơn giá (GIẢ ĐỊNH đàm phán).", [s_bmp2, s_bmp1]),
 "tien-phong": dg("9 tháng 2026 NTP đạt doanh thu thuần 5.751,4 tỷ đồng (+18,11%), LNST 1.021,6 tỷ đồng (+29,31%); LNTT 1.232,8 tỷ đồng, bằng ~137% kế hoạch năm (900 tỷ). Hãng chủ động dự báo và kiểm soát tồn kho nguyên liệu trong bối cảnh khan hiếm hạt nhựa.",
     "Tài chính và nguồn cung ổn định – phù hợp làm nhà cung cấp chính/đối trọng với BMP cho gói ống cấp thoát nước 2027; có thể đề nghị khóa giá theo quý (GIẢ ĐỊNH).", [s_ntp]),
 "viglacera": dg("Quý III/2026 Viglacera lãi sau thuế hơn 616 tỷ đồng (gấp ~5,2 lần), doanh thu gần 3.795 tỷ (+17%); 9 tháng mảng gạch ốp lát đạt hơn 3.075 tỷ (+12%), kính & gương hơn 2.109 tỷ (+49%) và chuyển sang có lãi. Tồn kho hơn 10.413 tỷ đồng (~39% tổng tài sản).",
     "Mảng kính hồi phục mạnh → ít dư địa giảm giá kính nổi; gạch/sứ vẫn có thể đàm phán theo sản lượng dự án (GIẢ ĐỊNH).", [s_vgc]),
 "an-cuong": dg("9 tháng 2026 An Cường đạt doanh thu 3.550,8 tỷ đồng (+20,8%), LNST 424,7 tỷ (+18,6%); tài sản dở dang dài hạn lên 1.479,1 tỷ (gấp hơn 44 lần đầu năm), nợ vay dài hạn 1.121,9 tỷ – đang đầu tư mở rộng năng lực.",
     "Năng lực sản xuất tủ bếp/ván cho dự án sắp tăng – có thể đàm phán tiến độ và giá cho gói 2027; theo dõi đòn bẩy, hạn chế tạm ứng lớn.", [s_acg]),
 "dulux": dg("AkzoNobel công bố (05/10/2026) bán mảng sơn trang trí Dulux tại Việt Nam và 6 thị trường khác cho Nippon Paint với giá 1,35 tỷ USD; phần ngoài Indonesia dự kiến hoàn tất khoảng giữa 2027, chờ phê duyệt.",
     "Hợp đồng khung Dulux kéo sang 2027: thêm điều khoản đổi chủ sở hữu (giữ giá, bảo hành, mã sản phẩm); giữ Jotun/TOA trong danh sách mời thầu vì thị trường sơn sẽ tập trung hơn.", [s_dulux]),
 "nippon-paint": dg("Nippon Paint mua mảng sơn trang trí Dulux của AkzoNobel tại VN và Đông Nam Á (1,35 tỷ USD, công bố 05/10/2026; phần lớn hoàn tất khoảng giữa 2027) – sau thương vụ Nippon sẽ nắm cả hai thương hiệu lớn.",
     "Thị phần tập trung làm giảm cạnh tranh giữa Nippon và Dulux trong cùng gói thầu → không nên coi hai hãng là hai nhà thầu độc lập từ 2027 (GIẢ ĐỊNH).", [s_dulux]),
 "jotun": dg("Gia Lai khởi tố vụ buôn bán sơn, bột trét giả nhãn hiệu Jotun: thu giữ 53 thùng sơn và 49 bao bột trét không hóa đơn chứng từ tại một cửa hàng ở phường An Nhơn Nam.",
     "Với gói sơn do nhà thầu cung cấp: bắt buộc CO/CQ theo lô, mua qua nhà phân phối được Jotun xác nhận và lấy mẫu kiểm tra tại công trường.", [s_jotun]),
 "cadisun": dg("TAND Hà Nội (28/8/2026) xử 6 bị cáo tại Cadisun về vi phạm quy định kế toán (2 hệ thống sổ sách 2020–2023), gây thiệt hại ngân sách hơn 405 tỷ đồng; Chủ tịch kiêm TGĐ nhận 5 năm tù, PTGĐ 4 năm tù và đã kháng cáo.",
     "Rủi ro quản trị/pháp lý nhà cung cấp: nếu còn dùng Cadisun, yêu cầu hóa đơn đầy đủ, bảo lãnh thực hiện và chuẩn bị phương án thay thế (Cadivi, LS-VINA, Trần Phú).", [s_cadisun]),
 "taya": dg("Quý III/2026 Taya Việt Nam có doanh thu 860 tỷ đồng (+53%), LNST 25,1 tỷ; 9 tháng dòng tiền kinh doanh âm gần 290 tỷ đồng, nợ vay 1.189 tỷ (+38,7%), toàn bộ ngắn hạn.",
     "Biên lợi nhuận mỏng, phụ thuộc vay ngắn hạn → hạn chế tạm ứng, ưu tiên thanh toán theo giao hàng.", [s_taya]),
 "taicera": dg("Quý III/2026 Taicera lãi 6 tỷ đồng nhưng 9 tháng vẫn lỗ 20 tỷ (doanh thu 648 tỷ, +1%); lỗ lũy kế hơn 234 tỷ đồng.",
     "Sức khỏe tài chính yếu: nếu chọn Taicera cho gạch trung cấp, tránh tạm ứng lớn, yêu cầu bảo lãnh và tồn kho đủ cho cả dự án.", [s_tcr]),
 "inax": dg("LIXIL/INAX kỷ niệm 30 năm tại VN, ra mắt dòng Spalet Clean (bồn cầu và nắp rửa thông minh, lắp được trên bồn cầu có sẵn) và chạy flash sale giảm tới 40% tại 105 showroom/đại lý từ 10/2026 đến 01/2027.",
     "Mức giảm bán lẻ tới 40% là mốc tham chiếu khi đàm phán đơn giá nắp rửa điện tử/bồn cầu cho dự án trung cấp.", [s_inax]),
 "hettich": dg("Hettich Việt Nam ký MOU (13/10/2026) với Han Spaces để tích hợp phụ kiện nội thất (bản lề, ray trượt, hệ chuyển động) vào các hạng mục dự án nhà ở, kèm tư vấn kỹ thuật và cam kết nguồn cung.",
     "Hettich đang đẩy kênh dự án → mời chào giá song song với Blum cho gói phụ kiện tủ bếp/tủ áo căn hộ cao cấp.", [s_hettich]),
 "schindler": dg("Schindler kỷ niệm 30 năm tại VN (từ 1996), giới thiệu nền tảng nội thất cabin DECO 3.0, giải pháp Phygital và Trung tâm vận hành kỹ thuật (TOC) kết nối dữ liệu thiết bị theo thời gian thực cho bảo trì.",
     "Đưa yêu cầu giám sát từ xa/TOC và chỉ số thời gian phản hồi vào hợp đồng bảo trì khi chấm thầu thang máy.", [s_schindler]),
 "samsung": dg("Samsung đẩy mạnh B2B điều hòa tại VN: mở rộng đại lý, xây năng lực tư vấn – thiết kế, tham gia sớm từ khâu quy hoạch dự án; tham chiếu Sycamore (~3.000 dàn WindFree) và Starlake (hơn 3.000 thiết bị cho ~600 căn). Toàn cầu, Samsung đang mua FläktGroup (HVAC trung tâm).",
     "Mời Samsung tham gia sớm gói điều hòa căn hộ để lấy giá dự án cạnh tranh với Daikin/LG (GIẢ ĐỊNH đàm phán).", [s_samsung]),
 "panasonic": dg("Panasonic Việt Nam đưa thương hiệu SANYO trở lại với dòng điều hòa Comfort Series, giá dễ tiếp cận, sản xuất tại nhà máy Panasonic ở Malaysia.",
     "SANYO là phương án phổ thông cho khu phụ trợ/căn hộ trung cấp; không thay thế dòng Panasonic cho dự án cao cấp.", [s_sanyo]),
}
# ---------- Digest danh mục
CD = {
 "mep.ong-nuoc": dg("Hạt PVC đắt làm biên gộp Bình Minh giảm xuống ~40% trong quý III, hãng cắt mạnh hỗ trợ đại lý; ngược lại Tiền Phong tăng trưởng mạnh và lần đầu sau 5 năm vượt BMP về lợi nhuận.",
     "Thời điểm tốt để đấu thầu cạnh tranh BMP – NTP cho gói ống 2027 và chốt giá sớm khi giá nhựa còn biến động.", [s_bmp2, s_ntp, s_bmp1]),
 "ht.son": dg("Thị trường sơn trang trí sắp tập trung: Nippon Paint mua mảng Dulux ĐNA (gồm VN) 1,35 tỷ USD, hoàn tất khoảng giữa 2027. Hàng giả Jotun tiếp tục bị phát hiện ở địa phương (Gia Lai).",
     "Giữ ít nhất một hãng độc lập (Jotun/TOA/Kova) trong mỗi gói sơn; siết CO/CQ theo lô với sơn do nhà thầu cấp.", [s_jotun, s_dulux]),
 "mep.cap-dien": dg("Rủi ro nhà cung cấp nổi lên: lãnh đạo Cadisun bị kết án vì sai phạm kế toán (thiệt hại ngân sách >405 tỷ), Taya dòng tiền âm và nợ vay ngắn hạn tăng. Taihan (Hàn Quốc) xây nhà máy cáp 400 kV tại Đồng Nai, dự kiến vận hành 2027.",
     "Rà soát lại danh sách nhà cung cấp cáp: ưu tiên hãng tài chính lành mạnh, thanh toán theo giao hàng với hãng có dòng tiền yếu.", [s_taihan, s_taya, s_cadisun]),
 "ht.gach-da": dg("Viglacera hồi phục mạnh (gạch ốp lát 9 tháng +12%), trong khi Taicera vẫn lỗ lũy kế hơn 234 tỷ đồng.",
     "Phân tầng rủi ro: dùng Viglacera/Prime cho khối lượng lớn, hạn chế tạm ứng với nhà cung cấp lỗ lũy kế.", [s_vgc, s_tcr]),
 "ht.tbvs": dg("Bồn cầu thông minh là chiến trường chính: INAX ra Spalet Clean và giảm giá tới 40% dịp 30 năm; JOMOO (TQ) đã có công ty con và showroom flagship ở Hà Nội; Uuviet mở showroom Hà Nội trưng bày Brizo/Axent/Innoci.",
     "Mở rộng danh sách mời thầu bồn cầu/nắp rửa điện tử trung–cao cấp (INAX, TOTO, JOMOO) để tạo áp lực giá (GIẢ ĐỊNH).", [s_inax, s_jomoo1, s_uu2]),
 "mep.hvac": dg("Các hãng Hàn – Nhật đẩy kênh dự án: Samsung xây năng lực tư vấn – thiết kế và tham gia sớm dự án; Panasonic đưa SANYO trở lại phân khúc giá dễ tiếp cận; Haier mua Ferroli ASEAN (nhà máy Thạch Thất).",
     "Mời ít nhất một hãng Hàn (Samsung/LG) cạnh tranh với Daikin/Mitsubishi cho gói điều hòa căn hộ.", [s_samsung, s_sanyo]),
}
for b in d["brands"]:
    if b["id"] in B: b["digest"] = B[b["id"]]
for c, v in CD.items():
    assert c in d["cats"]; d["cats"][c]["digest"] = v
cut = (date.fromisoformat(TODAY) - timedelta(days=60)).isoformat()
for o in list(d["brands"]) + list(d["cats"].values()):
    if o.get("digest") and o["digest"]["date"] < cut: del o["digest"]

# ---------- (B) Thương hiệu mới nổi
E = {e["id"]: e for e in d.get("emerging", [])}
def put(**e):
    e = nz(e); e["sources"] = sorted(e["sources"], key=lambda s: s["date"], reverse=True)
    if e["id"] in E: e["first_seen"] = E[e["id"]].get("first_seen", e["first_seen"])
    E[e["id"]] = e
put(id="taihan", name="Taihan Cable (Taihan Cable Vina)", origin="Hàn Quốc", note="Nhà máy cáp siêu cao áp KCN Long Thành (Đồng Nai), dự kiến vận hành 2027",
    kws=["taihan"], query='"Taihan"', tax={"mep.cap-dien": "cao-cap"}, signal="mo-rong", first_seen=TODAY, date="2026-11-09",
    why="Taihan Cable Vina xây nhà máy cáp 400 kV tại KCN Long Thành, vốn khoảng 75 tỷ won (~1.400 tỷ đồng), diện tích ~56.200 m², mục tiêu vận hành năm 2027 – sẽ là đơn vị duy nhất tại VN sản xuất được cáp 400 kV.",
    impl="Chủ yếu liên quan cáp trung/cao thế cho trạm biến áp và đấu nối dự án; thêm vào danh sách mời thầu cáp trung thế từ 2027 để đối trọng LS-VINA/Cadivi.",
    sources=[s_taihan])
put(id="alcorest", name="Alcorest (Nhôm Việt Dũng)", origin="Việt Nam", note="Tấm nhôm composite (ACP), trần nhôm, lam chắn nắng",
    kws=["alcorest", "nhom viet dung"], query='"Alcorest" OR "Nhôm Việt Dũng"', tax={"md.mat-dung": "trung-cap"}, signal="mo-rong", first_seen=TODAY, date="2026-11-07",
    why="Khánh thành nhà máy thứ 3 (06/11/2026) tại KCN Bá Thiện I (Phú Thọ), hơn 100.000 m², nâng tổng công suất lên gần 20 triệu m²/năm; có hơn 100 đại lý cấp 1 và xuất khẩu sang Đài Loan, Hàn Quốc, Úc, Canada.",
    impl="Phương án nội địa cho tấm ACP/trần nhôm/lam ở hạng mục phụ, giúp ép giá Alucobond/Alpolic; cần kiểm tra chứng nhận chống cháy trước khi đưa vào mặt dựng.",
    sources=[s_alco])
put(id="jomoo", name="JOMOO", origin="Trung Quốc", note="Bồn cầu thông minh, sen vòi; công ty con và showroom flagship tại Hà Nội",
    kws=["jomoo"], query='"JOMOO"', tax={"ht.tbvs": "trung-cap"}, signal="mo-rong", first_seen=TODAY, date="2026-11-03",
    why="Hãng bồn cầu thông minh lớn của Trung Quốc đã lập công ty con tại VN, vận hành showroom flagship ở Hà Nội và có khoảng 300 cửa hàng/Keyshop trên cả nước; vừa mở rộng sang thị trường Nhật Bản.",
    impl="Mời chào giá nắp rửa/bồn cầu thông minh cho căn hộ trung cấp để tạo áp lực lên INAX/TOTO; yêu cầu mẫu thử và chính sách bảo hành tại VN.",
    sources=[s_jomoo1, s_jomoo2])
put(id="uuviet-luxury", name="Brizo / Axent / Innoci (Uuviet Solutions)", origin="Âu – Mỹ", note="Nhà phân phối Uuviet Solutions (từ 2010, >20 thương hiệu Âu – Mỹ)",
    kws=["brizo", "axent", "innoci", "uuviet"], query='"Brizo" OR "Axent" OR "Innoci" OR "Uuviet"', tax={"ht.tbvs": "hang-sang"}, signal="mo-rong", first_seen=TODAY, date="2026-10-12",
    why="Uuviet Solutions khai trương showroom Hà Nội (10/10/2026, Vincom Mega Mall Royal City) với khu Luxury trưng bày Brizo, Delta, Axent (bồn cầu thông minh), BagnoDesign và khu Lifestyle có Innoci; Innoci đã được dùng cho dự án Lumi Hà Nội.",
    impl="Bổ sung nhóm thương hiệu Mỹ/Âu qua Uuviet vào danh sách mời thầu TBVS hạng sang bên cạnh Gessi/Axor để có thêm lựa chọn cho căn hộ hạng sang.",
    sources=[s_uu1, s_uu2])
put(id="fotile", name="FOTILE", origin="Trung Quốc", note="Văn phòng tại The Flemington Tower, TP.HCM",
    kws=["fotile"], query='"Fotile"', tax={"ht.thiet-bi-bep": "cao-cap"}, signal="vao-vn", first_seen=TODAY, date="2026-09-08",
    why="Hãng thiết bị bếp cao cấp Trung Quốc đưa sản phẩm cao cấp đầu tiên vào VN là lò hấp nướng E3 (hơn 50 chương trình nấu cài sẵn), đặt văn phòng tại TP.HCM.",
    impl="Theo dõi; có thể mời chào giá thử cho gói bếp căn hộ cao cấp để so với Bosch/Siemens khi hãng có nhà phân phối và dịch vụ bảo hành rõ ràng.",
    sources=[s_fotile])
cut90 = (date.fromisoformat(TODAY) - timedelta(days=90)).isoformat()
d["emerging"] = sorted([e for e in E.values() if e["date"] >= cut90], key=lambda e: e["date"], reverse=True)
C = set(d["cats"]); T = {t["id"] for t in d["tiers"]}; R = {b["id"] for b in d["brands"]}
assert all(c in C and t in T for e in d["emerging"] for c, t in e["tax"].items()) and not (R & {e["id"] for e in d["emerging"]})
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("brand digests:", sum(1 for b in d["brands"] if b.get("digest")), "cat digests:", sum(1 for c in d["cats"].values() if c.get("digest")), "emerging:", len(d["emerging"]))
