# Rà soát thứ Hai 23/11/2026: vá trends/data/scm.json hiện hành (tiếp nối scm_2026-11-16.py).
# Không đổi signal/trend. Cập nhật: cáp điện (đồng LME 3 tháng −8,2%/tuần, thấp nhất từ 24/3), nhôm/kính (LME 3 tháng −~6%/tuần, backwardation rộng),
# thép (giá VN đứng tuần thứ tư; quặng TQ −2,1%/tuần; AD25 hạn bảng câu hỏi 30/11; rà soát phạm vi CBPG thép mạ AD19; nhận hồ sơ rà soát cáp DƯL AD17),
# cát/đá (giá Q3 HN, TP.HCM theo VCCI 12/11), xi măng (Phú Thọ), tủ bếp (nhận hồ sơ rà soát CBPG ván MDF AD21), cước (SCFI 20/11, Brent).
import json, unicodedata
N = lambda s: unicodedata.normalize("NFC", s)
p = "trends/data/scm.json"; d = json.load(open(p, encoding="utf-8"))
d["updated"] = "2026-11-23"
d["freight"]["text"] = N("Cước biển Shanghai → TP.HCM 10/2026: 20GP 645–900 USD, 40HQ 1.190–1.600 USD; → Hải Phòng: 20GP 650–830 USD, 40HQ 1.060–1.560 USD (chưa phí địa phương; TSL cập nhật 15/10, rà soát 23/11 chưa có bảng mới). SCFI 20/11: 3.503,78 điểm (−1,91% tuần), tuần giảm thứ ba liên tiếp, thủng mốc 3.500; tuyến Viễn Đông → Đông Nam Á gần như đi ngang 1.152 USD/TEU (+2 USD). Hãng tàu dự kiến cước còn chịu áp lực giảm tới khoảng giữa tháng 12, sau đó có thể bật tăng ngắn trước Tết Nguyên đán → nên book hàng TQ cần về trước Tết từ đầu tháng 12. Brent 92,57 USD/thùng (20/11), giảm tuần thứ ba (−3,41% tuần) → phụ phí nhiên liệu tiếp tục dịu.")
d["freight"]["source"] = {"name": "TSL – cước Shanghai → VN (cập nhật 15/10/2026; rà soát 23/11/2026: SCFI 20/11 qua BigGo Finance, Brent qua Market Times 21/11)", "url": "https://tsl.com.vn/gia-cuoc-van-chuyen-tu-shanghai-ve-viet-nam/", "date": "2026-10-15"}
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
MT21 = ("Market Times 21/11/2026 – thị trường hàng hóa (LME, Brent)", "https://markettimes.vn/thi-truong-ngay-21-11-vang-van-o-day-14-thang-dau-giam-tuan-thu-ba-lien-tiep-dong-mat-hon-8-134698.html", "2026-11-21")
MTW = ("Market Times 22/11/2026 – thị trường tuần 16–21/11", "https://markettimes.vn/thi-truong-tuan-qua-16-21-11-vang-bac-dong-bitcoin-bi-ban-thao-dau-giam-tuan-thu-ba-lien-tiep-134725.html", "2026-11-22")
VCCI = ("VCCI 12/11/2026 – giá VLXD tăng cuối năm", "https://vcci.com.vn/tin-tuc/gia-vat-lieu-xay-dung-tang-cuoi-nam-xay-nha-co-the-doi-chi-phi-bao-nhieu", "2026-11-12")
PV = "https://pvtm.gov.vn/default.aspx?page=news-detail&do=detail&category_id=91b07cf1-3658-4f39-b688-73b9e8ff8a05&id="

# Thép – giá VN đứng tuần thứ tư; quặng TQ tiếp tục giảm; PVTM
c = C["thep"]
c["headline"] = N("VN tự chủ thép cây; giá nội địa đứng yên tuần thứ tư (13.840–15.150 đ/kg tùy hãng/miền, 21/11) trong khi quặng sắt TQ giảm thêm ~2,1%/tuần (Đại Liên 659 NDT/tấn, Singapore 88,5 USD/tấn) và thép cây SHFE quanh 3.026 NDT/tấn → áp lực giảm hơn là tăng.")
drop(c["supply"], "Giá thép VN 15/11 ổn định")
add(c["supply"], "Giá thép VN 21/11 ổn định cả 3 miền (13.840–15.150 đ/kg): Bắc CB240 Việt Đức 14.650, Hòa Phát 14.920, VAS 14.950 đ/kg; D10 CB300 VAS 13.840, Hòa Phát 14.210 đ/kg; Trung Việt Đức CB240 15.150 đ/kg; Nam Hòa Phát D10 14.720, VAS/TungHo 13.840 đ/kg (DNHN, số liệu SteelOnline)")
add(c["demand"], "TQ tuần 16–20/11/2026: thép cây SHFE kỳ hạn 12/2026 đóng 20/11 ở 3.026 NDT/tấn; quặng sắt Đại Liên 659 NDT/tấn (−2,09%/tuần, đáy 638,5 ngày 18/11), Singapore 88,5 USD/tấn (−2,16%/tuần); tồn kho quặng tại cảng TQ 157,36 triệu tấn (+0,74%); Minmetals Futures dự báo giá đi ngang biên độ hẹp tuần tới")
add(c["trade"], "PVTM 10–13/11/2026: AD25 inox cán nguội (TQ, Indonesia, Đài Loan) – hạn nộp bảng câu hỏi của nhà xuất khẩu 30/11/2026 (TB 234/TB-PVTM); chấp nhận hồ sơ rà soát phạm vi sản phẩm CBPG thép mạ AD19 (TQ, Hàn Quốc; QĐ 2310/QĐ-BCT) theo TB 232/TB-PVTM; nhận hồ sơ đề nghị rà soát CBPG cáp thép DƯL AD17 (Malaysia, Thái Lan, TQ) đến 10/12/2026")
c["rec_detail"] = N("Mua thép cây từ nhà máy VN (giá giao tận công trình, không rủi ro phòng vệ thương mại). 23/11: giá đứng 4 tuần, quặng TQ tiếp tục giảm → không mua gom; yêu cầu chiết khấu thêm theo khối lượng Q1/2027, giữ đơn giá cố định 30–60 ngày. Inox cán nguội (ốp cabin thang, bếp, lan can): vụ AD25 đang thu thập bảng câu hỏi (hạn 30/11) → chốt PO hàng nhập trước khi có thuế tạm thời hoặc chuyển NCC VN. Tôn mạ: đang rà soát phạm vi CBPG AD19 → hỏi NCC mã HS/quy cách có thuộc diện thuế không. Cáp DƯL: hàng Boxing Victory (TQ) nay chịu CBPG 4,47% → đưa vào so sánh giá. Thép hình/tấm: so sánh VN với nhập khẩu (Hàn Quốc/Nhật/ASEAN) sau thuế CBPG; TQ chỉ khi nhà xuất khẩu có mức thuế thấp.")
c["timing"] = N("Giá đi ngang, nguyên liệu TQ suy yếu → không cần mua sớm; chốt khung Q1/2027 khi nhà máy còn chiết khấu, theo dõi thuế tạm thời inox cán nguội (AD25, hạn bảng câu hỏi 30/11).")
dsrc(c, "Doanh nghiệp Hội nhập 15/11/2026")
src(c, "Cục PVTM 13/11/2026 – AD19 thép mạ: hồ sơ rà soát phạm vi hợp lệ", PV + "f697dc20-7fd8-4c7d-9f82-c5a8c97714e0", "2026-11-13")
src(c, "Cục PVTM 13/11/2026 – AD25 inox cán nguội: bảng câu hỏi", PV + "4e22b95e-09ff-43ee-9842-c957fb86744b", "2026-11-13")
src(c, "Doanh nghiệp Hội nhập 21/11/2026 – giá thép hôm nay", "https://doanhnghiephoinhap.vn/gia-thep-hom-nay-21112026-thep-tuan-qua-giam-chung-ca-tuan-hoi-phuc-nhe-phien-cuoi-154746.html", "2026-11-21")

# Xi măng – mặt bằng địa phương
c = C["xi-mang"]
add(c["supply"], "Phú Thọ (Sở XD): xi măng tăng ~3–5% từ đầu năm 2026; Hà Nội: giá xi măng tương đối ổn định (VCCI 12/11)")
src(c, *VCCI)

# Cát / đá – giá thực tế tại HN, TP.HCM
c = C["cat-da"]
add(c["supply"], "Giá thực tế (VCCI 12/11): Hà Nội Q3/2026 cát đen 281.818–365.000 đ/m³, cát vàng 636.364–700.000 đ/m³ (Sở XD); TP.HCM theo một nhà thầu: cát từ 450.000 lên 560.000 đ/m³, đá từ hơn 500.000 lên 750.000–780.000 đ/m³; Phú Thọ: cát +7–12%, đá +25–40% từ đầu năm")
c["rec_detail"] = N("Nội địa bắt buộc. Ưu tiên cát nghiền (đá xay) thay cát vàng cho bê tông, hợp đồng khung với mỏ có giấy phép. 23/11: giá cát/đá còn tăng (Bộ XD dự báo +3–8%; đá tại TP.HCM đã tăng mạnh) và giá công bố của Sở XD đi sau thị trường → ký khung khối lượng có trần giá cho Q1/2027 ngay; điều khoản điều chỉnh giá nên dựa chỉ số Bộ XD/Sở XD có độ trễ rõ ràng; dự án TP.HCM cần dự phòng chi phí đá cao hơn.")
src(c, *VCCI)

# Nhôm / kính – LME 3 tháng giảm mạnh, backwardation rộng
c = C["nhom-kinh"]
c["headline"] = N("Nhôm LME kỳ hạn 3 tháng giảm gần 6% tuần qua còn 2.831,5 USD/tấn (20/11) trong khi giá giao ngay vẫn ~3.184,5 USD/tấn – backwardation rất rộng do tồn kho LME thấp (220.350 tấn, 18/11); kính float TQ vẫn yếu; nhôm định hình TQ chịu CBPG 2,85–35,58% đến 2029.")
drop(c["supply"], "Nhôm LME giao ngay 3.155")
add(c["supply"], "Nhôm LME 20/11: giao ngay (chào bán) 3.184,5 USD/tấn, kỳ hạn 3 tháng 2.831,5 USD/tấn (−gần 6%/tuần); tồn kho LME 220.350 tấn (18/11, từ 226.350 tấn ngày 13/11); SMM dự báo LME 3.020–3.180 USD/tấn, hợp đồng tháng 11 đáo hạn 18/11 có dấu hiệu ép giá (squeeze) (Market Times, AlCircle, SMM)")
c["rec_detail"] = N("Nhôm định hình: VN (hoặc nhà xuất khẩu TQ có mức CBPG thấp, kiểm tra tên trong QĐ 2531). Gắn giá nhôm theo LME 3 tháng (thấp hơn giao ngay ~350 USD/tấn ngày 20/11) thay vì giá giao ngay — NCC báo giá theo giá giao ngay là đang tính thêm phần backwardation. Kính hộp Low-E: so sánh VN (Viglacera, CFG) với TQ — TQ đang dư cung, chưa thấy CBPG kính TQ của VN; chi phí vỡ/hỏng vận chuyển cần tính vào.")
dsrc(c, "Market Times 14/11/2026")
src(c, "SMM 12/11/2026 – tổng kết tuần giá nhôm", "https://news.metal.com/newscontent/B5OVGECWZQUEGWYO4P4KSJ4MOS72V54FL643T4Y-macro-front-weakens-lme-squeeze-heats-up-smm-aluminum-price-weekly-review", "2026-11-12")
src(c, "AlCircle 19/11/2026 – LME nhôm 18/11", "https://www.alcircle.com/news/lme-aluminium-cash-offer-price-rises-1-1-to-3-095-t-as-opening-stocks-fall-to-220-350t-122016", "2026-11-19")
src(c, *MTW)
src(c, *MT21)

# Cáp điện – đồng LME −8,2%/tuần
c = C["cap-dien"]
c["headline"] = N("Đồng LME lao dốc: kỳ hạn 3 tháng có lúc còn 12.202 USD/tấn (20/11) – thấp nhất từ 24/3/2026, giảm ~8,2% trong tuần (mạnh nhất từ 4/2025) do kỳ vọng nhu cầu hạ tầng AI yếu đi, USD mạnh → giá đồng đã thấp hơn đỉnh 08/09 (~14.533 USD/tấn) khoảng 16%; có cơ sở đòi NCC cáp giảm giá.")
drop(c["supply"], "Đồng LME giao ngay ~13.711")
add(c["supply"], "Đồng LME 20/11: kỳ hạn 3 tháng có lúc giảm 4% còn 12.202 USD/tấn (thấp nhất từ 24/3/2026), giao ngay (chào bán chính thức) 12.230,5 USD/tấn; cả tuần −~8,2% (từ ~13.711 USD/tấn giao ngay ngày 13/11); nguyên nhân: nghi ngại định giá cổ phiếu công nghệ/AI, USD mạnh, kỳ vọng Fed tăng lãi suất tháng 12 (Market Times 21–22/11)")
c["rec_detail"] = N("Cáp hạ thế/trung thế: nhà máy VN (giá chiết khấu đại lý 30–40% tham khảo). Ký giá gắn LME đồng + phí gia công; hedge khối lượng lớn. 23/11: đồng đã giảm ~16% từ đỉnh 08/09 và ~12% trong 2 tuần (từ 13.955 USD/tấn ngày 06/11) → yêu cầu NCC báo lại giá theo LME hiện hành ngay (bảng giá cố định lập khi đồng cao hơn), chốt một phần gói Q1/2027 ở vùng giá này theo LME trung bình tháng; phần còn lại để mở vì xu hướng chưa dừng.")
c["timing"] = N("Đồng giảm mạnh → cơ hội chốt một phần (30–50%) khối lượng Q1/2027 theo công thức LME; phần còn lại chốt từng đợt, tránh giá cố định dài hạn.")
dsrc(c, "Market Times 14/11/2026"); dsrc(c, "Sina/Tân Kinh báo 14/11/2026")
src(c, *MTW)
src(c, *MT21)

# Tủ bếp – rà soát CBPG ván MDF
c = C["tu-bep"]
add(c["trade"], "Cục PVTM 10/11/2026: nhận hồ sơ đề nghị rà soát biện pháp CBPG ván sợi gỗ (MDF) từ Thái Lan, TQ (AD21, QĐ 121/QĐ-BCT ngày 19/01/2026) đến 09/12/2026 → mức thuế với từng nhà xuất khẩu có thể thay đổi")
src(c, "Cục PVTM 10/11/2026 – AD21 ván MDF: nhận hồ sơ rà soát", PV + "b377101a-082c-4f76-9fcf-f7937a693516", "2026-11-10")

json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("ok", len(d["categories"]))
