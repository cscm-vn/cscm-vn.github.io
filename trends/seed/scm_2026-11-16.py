# Rà soát thứ Hai 16/11/2026: vá trends/data/scm.json hiện hành (tiếp nối scm_2026-11-09.py).
# Đổi: cáp điện trend flat→down (đồng LME xuống đáy 4 tháng 13.515 USD/tấn trong phiên 12/11).
# Cập nhật: thép (giá VN đứng, quặng/thép TQ yếu, XK thép TQ T10 −6,1% m/m; điều tra CBPG inox cán nguội AD25; giảm CBPG cáp thép DƯL Boxing Victory),
# xi măng & cát/đá & bê tông (giá BQ T10 của Bộ XD + dự báo cuối năm), nhôm/kính, ống nhựa (Tiền Phong 9T), điều hòa (REE M&E), MBA (XK MBA TQ 9T), TBVS (timing), cước.
import json, unicodedata
N = lambda s: unicodedata.normalize("NFC", s)
p = "trends/data/scm.json"; d = json.load(open(p, encoding="utf-8"))
d["updated"] = "2026-11-16"
d["freight"]["text"] = N("Cước biển Shanghai → TP.HCM 10/2026: 20GP 645–900 USD, 40HQ 1.190–1.600 USD; → Hải Phòng: 20GP 650–830 USD, 40HQ 1.060–1.560 USD (chưa phí địa phương; TSL cập nhật 15/10, rà soát 16/11 chưa có bảng mới). SCFI 13/11: 3.572,33 điểm (−1,7% tuần), tuần giảm thứ hai liên tiếp – thị trường xuất khẩu TQ \"cơ bản ổn định, đa số tuyến điều chỉnh giảm\" (SSE); mùa thấp điểm tháng 11 → cước nội Á không có lực tăng. Rủi ro phụ phí nhiên liệu dịu đi: Brent 96,28 USD/thùng (13/11), giảm tuần thứ hai, so với 117,64 USD/thùng (30/10); Hormuz vẫn có sự cố tàu chở dầu.")
d["freight"]["source"] = {"name": "TSL – cước Shanghai → VN (cập nhật 15/10/2026; rà soát 16/11/2026: SCFI 13/11 qua Jiemian/SSE, Brent qua Market Times 14/11)", "url": "https://tsl.com.vn/gia-cuoc-van-chuyen-tu-shanghai-ve-viet-nam/", "date": "2026-10-15"}
C = {c["id"]: c for c in d["categories"]}
def add(lst, s):  # bullet mới lên đầu
    s = N(s)
    if s not in lst: lst.insert(0, s)
def drop(lst, prefix):
    lst[:] = [x for x in lst if not x.startswith(N(prefix))]
def src(c, name, url, date):
    if all(x["url"] != url for x in c["sources"]): c["sources"].insert(0, dict(name=N(name), url=url, date=date))
def dsrc(c, name_prefix):
    c["sources"][:] = [x for x in c["sources"] if not x["name"].startswith(N(name_prefix))]
BXD = ("VietnamPlus 10/11/2026 – giá VLXD tháng 10 (Bộ XD)", "https://www.vietnamplus.vn/gia-cac-loai-vat-lieu-xay-dung-van-neo-cao-du-bao-tiep-tuc-tang-post1147414.vnp", "2026-11-10")
VTV = ("VTV 11/11/2026 – tăng cường kiểm soát thị trường VLXD", "https://vtv.vn/tang-cuong-kiem-soat-thi-truong-vat-lieu-xay-dung-100261110204410844.htm", "2026-11-11")
NBS = ("Sina/Tân Kinh báo 14/11/2026 – NBS giá tư liệu sản xuất thượng tuần 11", "https://k.sina.cn/article_1644114654_61ff32de02002dcyo.html", "2026-11-14")
MT = ("Market Times 14/11/2026 – thị trường hàng hóa (LME, Brent)", "https://markettimes.vn/thi-truong-ngay-14-11-dau-giam-tuan-thu-hai-lien-tiep-vang-lao-doc-dong-cham-day-4-thang-ca-phe-phuc-hoi-manh-134407.html", "2026-11-14")

# Thép – giá VN tiếp tục đứng; nguyên liệu TQ giảm sâu; PVTM mới
c = C["thep"]
c["headline"] = N("VN tự chủ thép cây; giá nội địa đứng yên tuần thứ ba (D10 CB300 13.840–14.720 đ/kg tùy hãng/miền, 15/11) trong khi quặng sắt TQ giảm tuần sâu nhất 5 tuần và thép cây SHFE quanh 3.031–3.048 NDT/tấn → áp lực giảm hơn là tăng.")
drop(c["supply"], "Giá thép VN 09/11 ổn định")
add(c["supply"], "Giá thép VN 15/11 ổn định cả 3 miền: Bắc CB240 14.650 (Việt Đức)–14.950 đ/kg (VAS), D10 CB300 13.840 (VAS)–14.210 đ/kg (Hòa Phát); Trung CB240 Việt Đức 15.150, Hòa Phát 14.920, VAS 15.050 đ/kg; Nam Hòa Phát D10 14.720, VAS/TungHo 13.840 đ/kg (DNHN)")
drop(c["demand"], "TQ cuối 10/2026: thép cây")
add(c["demand"], "TQ thượng tuần 11/2026: thép cây Φ20 HRB400E 3.152,4 NDT/tấn (−0,5% so với cuối 10) – NBS; SHFE tuần 9–13/11 quanh 3.031–3.048 NDT/tấn (−0,2%), quặng sắt giảm 2,54–2,84%/tuần (Đại Liên 669,5 NDT/tấn, Singapore 90,45 USD/tấn), tồn kho quặng 10 cảng lớn 107,96 triệu tấn (+3,13%)")
add(c["trade"], "Xuất khẩu thép thành phẩm TQ T10/2026: 9,854 triệu tấn (−6,1% m/m, +0,74% n/n); 10T/2026: 95,495 triệu tấn (−2,3% n/n) – GACC qua SteelOrbis")
add(c["trade"], "PVTM 06/11/2026: Bộ Công Thương mở điều tra CBPG thép không gỉ cán nguội từ TQ, Indonesia, Đài Loan (QĐ 2948/QĐ-BCT, AD25, HS 7219/7220; hạn đăng ký bên liên quan 05/01/2027); rà soát lần 1 CBPG cáp thép dự ứng lực (Malaysia, Thái Lan, TQ): nhóm Boxing Victory (TQ) giảm còn 4,47% (trước 9,79–28%)")
c["rec_detail"] = N("Mua thép cây từ nhà máy VN (giá giao tận công trình, không rủi ro phòng vệ thương mại). 16/11: giá đứng 3 tuần, nguyên liệu TQ giảm → không mua gom; yêu cầu chiết khấu thêm theo khối lượng Q1/2027, giữ đơn giá cố định 30–60 ngày. Inox cán nguội (ốp cabin thang, bếp, lan can): VN đang điều tra CBPG hàng TQ/Indonesia/Đài Loan → chốt PO hàng nhập trước khi có thuế tạm thời hoặc chuyển NCC VN. Cáp DƯL: hàng Boxing Victory (TQ) nay chịu CBPG 4,47% → đưa vào so sánh giá. Thép hình/tấm: so sánh VN với nhập khẩu (Hàn Quốc/Nhật/ASEAN) sau thuế CBPG; TQ chỉ khi nhà xuất khẩu có mức thuế thấp.")
c["timing"] = N("Giá đi ngang, nguyên liệu TQ suy yếu → không cần mua sớm; chốt khung Q1/2027 khi nhà máy còn chiết khấu, theo dõi thuế tạm thời inox cán nguội (AD25).")
dsrc(c, "Doanh nghiệp Hội nhập 09/11/2026"); dsrc(c, "NBS Trung Quốc – giá tư liệu sản xuất cuối 10/2026")
src(c, "Tạp chí Công Thương 07/11/2026 – điều tra CBPG inox cán nguội (AD25)", "https://tapchicongthuong.vn/bo-cong-thuong-dieu-tra-ap-dung-bien-phap-chong-ban-pha-gia-voi-thep-khong-gi-can-nguoi-564277.htm", "2026-11-07")
src(c, "Người Quan sát 06/11/2026 – rà soát CBPG cáp thép DƯL", "https://nguoiquansat.vn/nhom-doanh-nghiep-trung-quoc-ban-pha-gia-vao-viet-nam-bo-cong-thuong-co-quyet-dinh-moi-326535.html", "2026-11-06")
src(c, "SteelOrbis – xuất khẩu thép TQ 10T/2026", "https://www.steelorbis.com/steel-news/latest-news/chinas-steel-exports-down-23-in-jan-oct-down-61-in-oct-from-sept-2026-1489467.htm", "2026-11")
src(c, *NBS)
src(c, "Doanh nghiệp Hội nhập 15/11/2026 – giá thép hôm nay", "https://doanhnghiephoinhap.vn/gia-thep-hom-nay-15112026-thi-truong-thep-va-quang-sat-tuan-qua-giam-sau-154260.html", "2026-11-15")

# Xi măng – giá BQ T10 gần như đứng, Bộ XD dự báo +1–3%
c = C["xi-mang"]
add(c["supply"], "Bộ XD: giá xi măng bình quân cả nước T10/2026 ~2.222 đ/kg (+0,1% so với T9 và Q3); dự báo cuối năm tăng 1–3% do giá dầu, cước biển, tỷ giá")
c["timing"] = N("Không gấp — dư cung; Bộ XD dự báo chỉ +1–3% cuối năm → ký hợp đồng ngắn hạn theo quý, không chấp nhận tăng giá vượt biên độ này.")
src(c, *BXD)

# Cát / đá – giá BQ tăng, dự báo +3–8%
c = C["cat-da"]
c["headline"] = N("Cát khan hiếm, giá tiếp tục leo: cát xây dựng BQ cả nước T10/2026 ~1.013.250 đ/m³ (+2% m/m), đá ~618.324 đ/m³ (+1,04%); Bộ XD dự báo cát/đá tăng thêm 3–8% cuối năm; Hà Nội thiếu ~320 triệu m³ cát giai đoạn 2026–2030.")
add(c["supply"], "Bộ XD (10/11): T10/2026 cát xây dựng BQ ~1.013.250 đ/m³ (+2% m/m, +2,4% so với Q3), đá ~618.324 đ/m³ (+1,04% m/m); Q3 so với Q2: cát +2,92–5,57%, đá +3,89–5,83%; dự báo cuối năm cát, đá +3–8%")
add(c["demand"], "Bộ XD yêu cầu địa phương công bố giá kịp thời, rà soát trữ lượng mỏ, xử lý găm hàng/đầu cơ; đến 09/11 chỉ 7/34 địa phương công bố giá VLXD đến Q3 và 9/34 đến T10 → giá công bố trễ so với thị trường (VTV 11/11)")
c["rec_detail"] = N("Nội địa bắt buộc. Ưu tiên cát nghiền (đá xay) thay cát vàng cho bê tông, hợp đồng khung với mỏ có giấy phép. 16/11: giá cát/đá còn tăng (dự báo +3–8%) và giá công bố của Sở XD đi sau thị trường → ký khung khối lượng có trần giá cho Q1/2027 ngay; điều khoản điều chỉnh giá nên dựa chỉ số Bộ XD/Sở XD có độ trễ rõ ràng.")
src(c, *VTV)
src(c, *BXD)

# Bê tông – chi phí đầu vào cát/đá tăng
c = C["be-tong"]
add(c["supply"], "Chi phí đầu vào T10/2026 (Bộ XD): cát +2% m/m, đá +1,04%, xi măng +0,1% → áp lực điều chỉnh giá bê tông chủ yếu từ cốt liệu; dự báo cát/đá +3–8% cuối năm")
src(c, *BXD)

# Nhôm / kính
c = C["nhom-kinh"]
c["headline"] = N("Nhôm LME nhích lên 3.155 USD/tấn (giao ngay 13/11), tồn kho LME còn 226.350 tấn và chênh lệch giao ngay–3 tháng rộng nhất ~36 năm → nguồn nhôm ngắn hạn căng; kính float TQ vẫn yếu; nhôm định hình TQ chịu CBPG 2,85–35,58% đến 2029.")
drop(c["supply"], "Nhôm LME giao ngay 3.117")
add(c["supply"], "Nhôm LME giao ngay 3.155–3.155,5 USD/tấn, kỳ hạn 3 tháng ~3.030–3.032 USD/tấn (13/11); tồn kho LME 226.350 tấn (−~56% từ đầu năm), chênh lệch giao ngay so với 3 tháng rộng nhất ~36 năm (Market Times 14/11)")
c["rec_detail"] = N("Nhôm định hình: VN (hoặc nhà xuất khẩu TQ có mức CBPG thấp, kiểm tra tên trong QĐ 2531). Gắn giá nhôm theo LME 3 tháng (thấp hơn giao ngay ~120 USD/tấn) thay vì giá giao ngay. Kính hộp Low-E: so sánh VN (Viglacera, CFG) với TQ — TQ đang dư cung, chưa thấy CBPG kính TQ của VN; chi phí vỡ/hỏng vận chuyển cần tính vào.")
dsrc(c, "Westmetall – LME 06/11")
src(c, *MT)

# Cáp điện – đồng LME về đáy 4 tháng → trend down
c = C["cap-dien"]
c["trend"] = "down"
c["headline"] = N("Đồng LME giảm tuần thứ hai: giao ngay ~13.711 USD/tấn (13/11), kỳ hạn 3 tháng 13.588 USD/tấn, trong phiên 12/11 chạm 13.515 USD/tấn – thấp nhất từ 20/7/2026 (đỉnh ~14.533 USD/tấn ngày 08/09) → xu hướng chuyển giảm, có cơ sở đòi giảm giá cáp; Cadivi điều chỉnh bảng giá từ 06/04/2026.")
drop(c["supply"], "Đồng LME giao ngay 13.955")
add(c["supply"], "Đồng LME giao ngay ~13.711–13.712 USD/tấn, 3 tháng 13.588 USD/tấn (13/11), giảm từ 13.955 USD/tấn (06/11) do USD mạnh, lợi suất trái phiếu Mỹ tăng (Market Times 14/11); đồng điện phân TQ thượng tuần 11 109.779,3 NDT/tấn (−0,4%) – NBS")
c["rec_detail"] = N("Cáp hạ thế/trung thế: nhà máy VN (giá chiết khấu đại lý 30–40% tham khảo). Ký giá gắn LME đồng + phí gia công; hedge khối lượng lớn. 16/11: đồng giảm ~5,6% từ đỉnh 08/09 → yêu cầu NCC báo lại giá theo LME hiện hành (bảng giá Cadivi lập khi đồng thấp hơn nhưng chiết khấu dự án nên tăng), chốt từng đợt cho gói Q1/2027 theo LME trung bình tháng; chưa cố định giá dài hạn khi xu hướng còn giảm.")
c["timing"] = N("Đồng đang giảm → chia nhỏ đợt chốt giá, dùng công thức LME trung bình tháng; tránh giá cố định dài hạn.")
dsrc(c, "Westmetall – LME 06/11"); dsrc(c, "NBS Trung Quốc – giá tư liệu sản xuất cuối 10/2026")
src(c, *NBS)
src(c, *MT)

# Ống nhựa – Tiền Phong
c = C["ong-nhua"]
add(c["supply"], "Tiền Phong Q3/2026: doanh thu thuần 2.106,1 tỷ đồng (+30,85%), LN trước thuế 353,2 tỷ (+12,58%); 9T doanh thu 5.751,4 tỷ (+18,11%), doanh thu dự án +25%; công ty nêu nguồn hạt nhựa khan hiếm, phải quản trị tồn kho nguyên liệu (Tạp chí Công Thương 23/10)")
c["rec_detail"] = N("Nhà máy VN; ống PPR cao cấp có thể so với hàng TQ/Đức. Giá gắn bảng giá công bố − chiết khấu. Tiền Phong tăng mạnh doanh thu dự án trong khi Bình Minh giảm doanh số → mời cả hai chào giá cạnh tranh, đòi chiết khấu dự án và cam kết nguồn hàng khi hạt nhựa khan.")
src(c, "Tạp chí Công Thương 23/10/2026 – Nhựa Tiền Phong 9T", "https://tapchicongthuong.vn/nhua-tien-phong--loi-nhuan-9-thang-vuot-37--ke-hoach-nam-560316.htm", "2026-10-23")

# Điều hòa – cầu M&E
c = C["dieu-hoa"]
add(c["demand"], "REE M&E (cơ điện lạnh & thương mại) 9T/2026: doanh thu 3.208 tỷ đồng (+41%), LN sau thuế 205 tỷ (+86%), ký mới 9.069 tỷ đồng hợp đồng → nhà thầu cơ điện lớn đang đầy việc, nên chốt sớm năng lực lắp đặt HVAC (CafeF 30/10)")
src(c, "CafeF 30/10/2026 – REE 9T/2026", "https://cafef.vn/co-dien-lanh-ree-bao-doanh-thu-cao-nhat-lich-su-mang-bds-di-lui-188261030081005122.chn", "2026-10-30")

# MBA / máy phát
c = C["mba-may-phat"]
add(c["trade"], "Xuất khẩu MBA TQ 9T/2026 +22,5% n/n, dây & cáp điện +28,1% (Science and Technology Daily 27/10) → nhà máy TQ ưu tiên đơn xuất khẩu giá cao")
add(c["supply"], "EEMC (Đông Anh) xuất khẩu MBA 70 MVA 132/33 kV sang Úc, đã chế tạo MBA 500 kV 3×300 MVA → nhà sản xuất VN cũng nhận đơn xuất khẩu, slot sản xuất trong nước có thể căng (Tạp chí Công Thương 15/10)")
src(c, "Tạp chí Công Thương 15/10/2026 – EEMC", "https://tapchicongthuong.vn/magazine/eemc--tu-lam-chu-may-bien-ap-500-kv-den-khat-vong-vuon-xa-558132.htm", "2026-10-15")
src(c, "Science and Technology Daily 27/10/2026 – xuất khẩu TQ 9T", "https://www.stdaily.com/web/English/2026-10/27/content_602630.html", "2026-10-27")

# TBVS – Canton Fair đã qua
c = C["tbvs"]
c["timing"] = N("Canton Fair GĐ2 đã kết thúc (27/10) → dùng báo giá thu được làm giá đối chứng; chỉ số Phật Sơn thường công bố cuối tháng sau (T9 ra 27–28/10) — chốt gói không nhãn trước Tết khi giá xuất khẩu còn yếu.")
drop(c["trade"], "Chỉ số giá sứ vệ sinh Phật Sơn −9,47% m/m (6/2026)")
dsrc(c, "JC68 – chỉ số giá Phật Sơn 6/2026")

json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("ok", len(d["categories"]))
