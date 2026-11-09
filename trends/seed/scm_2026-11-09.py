# Rà soát thứ Hai 09/11/2026: vá trends/data/scm.json hiện hành (tiếp nối scm_2026-11-02.py).
# Đổi: cáp điện trend up→flat (đồng LME lùi về 13.955); thép trend up→flat (giá VN đi ngang, thép cây TQ giảm nhẹ).
import json, unicodedata
N = lambda s: unicodedata.normalize("NFC", s)
p = "trends/data/scm.json"; d = json.load(open(p, encoding="utf-8"))
d["updated"] = "2026-11-09"
d["freight"]["text"] = N("Cước biển Shanghai → TP.HCM 10/2026: 20GP 645–900 USD, 40HQ 1.190–1.600 USD; → Hải Phòng: 20GP 650–830 USD, 40HQ 1.060–1.560 USD (chưa phí địa phương; TSL cập nhật 15/10, rà soát 09/11 chưa có bảng mới). Giá spot Shanghai → Hải Phòng 20' 594–673 USD (Cogoport 06/11, chuyến 06–25/11). Nội Á ổn định: SCFI 06/11 tuyến Viễn Đông – Đông Nam Á −5 USD/TEU (−0,42%). SCFI tổng 3.633,45 (−53,9; −1,46%), dừng chuỗi 4 tuần tăng – mùa thấp điểm tháng 11. Rủi ro phụ phí: Hormuz (Brent 117,64 USD/thùng 30/10).")
d["freight"]["source"] = {"name": "TSL – cước Shanghai → VN (cập nhật 15/10/2026; rà soát 09/11/2026: Cogoport 06/11, SCFI 06/11)", "url": "https://tsl.com.vn/gia-cuoc-van-chuyen-tu-shanghai-ve-viet-nam/", "date": "2026-10-15"}
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
NBS = ("NBS Trung Quốc – giá tư liệu sản xuất cuối 10/2026 (04/11)", "https://www.stats.gov.cn/zwfwck/sjfb/202611/t20261103_1965738.html", "2026-11-04")

# Thép – giá VN đi ngang, TQ giảm nhẹ → trend flat
c = C["thep"]
c["trend"] = "flat"
c["headline"] = N("VN tự chủ thép cây; giá nội địa đi ngang đầu 11/2026 (D10 CB300 13.840–14.720 đ/kg tùy hãng/miền) sau đợt nhích tăng tháng 10; thép cây TQ giảm nhẹ.")
add(c["supply"], "Giá thép VN 09/11 ổn định: Hòa Phát CB240 14.920 đ/kg, D10 CB300 14.210 đ/kg (Bắc, Trung), 14.720 đ/kg (Nam); VAS/TungHo D10 CB300 13.840 đ/kg (SteelOnline qua DNHN)")
add(c["demand"], "TQ cuối 10/2026: thép cây Φ20 HRB400E 3.167,3 NDT/tấn (−0,6% so với giữa tháng), HRC 3.236,1 NDT/tấn (−1,0%) – NBS; SHFE thép cây ~3.046–3.060 NDT/tấn (09/11), cầu xuất khẩu hạ nhiệt")
c["rec_detail"] = N("Mua thép cây từ nhà máy VN (giá giao tận công trình, không rủi ro phòng vệ thương mại). 09/11: giá đứng yên, TQ yếu → không cần mua gom trước; đàm phán chiết khấu theo khối lượng, giữ đơn giá cố định 30–60 ngày. Thép hình/tấm: so sánh VN với nhập khẩu (Hàn Quốc/Nhật/ASEAN) sau thuế CBPG; TQ chỉ khi nhà xuất khẩu có mức thuế thấp.")
src(c, *NBS)
src(c, "Doanh nghiệp Hội nhập 09/11/2026 – giá thép hôm nay", "https://doanhnghiephoinhap.vn/gia-thep-hom-nay-9112026-thep-thanh-pham-trung-quoc-but-pha-153733.html", "2026-11-09")

# Xi măng – TQ nhích nhẹ, VN không đổi
c = C["xi-mang"]
add(c["trade"], "TQ cuối 10/2026: xi măng P.O42.5 rời 270,9 NDT/tấn (+1,5% so với giữa tháng) – NBS; vẫn thấp, clinker TQ dư để xuất")
src(c, *NBS)

# Cát / đá
c = C["cat-da"]
add(c["supply"], "Thiếu cát đắp 2026: dự án giao thông trọng điểm do Bộ XD quản lý thiếu >73 triệu m³, do địa phương quản lý thiếu gần 58 triệu m³, dự án khác gần 80 triệu m³; 6 địa phương không tự cân đối được: Hà Nội, Cần Thơ, Hưng Yên, Ninh Bình, Tây Ninh, Cà Mau – Vành đai 4 HN phải chở vật liệu từ tỉnh khác, xa tới Nghệ An (VTV 07/11)")
drop(c["demand"], "6 tỉnh/thành thiếu vật liệu")
add(c["demand"], "6 tỉnh/thành không tự cân đối vật liệu (Hà Nội, Cần Thơ, Hưng Yên, Ninh Bình, Tây Ninh, Cà Mau) – đầu tư công cạnh tranh nguồn với dự án tư nhân")
src(c, "VTV 07/11/2026 – thiếu vật liệu đe dọa tiến độ", "https://vtv.vn/thieu-vat-lieu-anh-huong-den-tien-do-cac-du-an-100261106223656645.htm", "2026-11-07")

# Nhôm / kính
c = C["nhom-kinh"]
c["headline"] = N("Nhôm LME đi ngang 3.117 USD/tấn (giao ngay 06/11); kính float TQ vẫn yếu (5/6 mm 1.069,9 NDT/tấn cuối 10/2026, −0,8%); nhôm định hình TQ chịu CBPG 2,85–35,58% đến 2029.")
for pre in ("Nhôm LME ~3.001,5", "Nhôm LME giao ngay 3.043", "Nhôm LME giao ngay 3.114"):
    drop(c["supply"], pre)
add(c["supply"], "Nhôm LME giao ngay 3.117 USD/tấn, tồn kho LME 227.600 tấn (06/11); nhôm A00 TQ cuối 10/2026 23.787,1 NDT/tấn (+0,9%) – NBS")
add(c["supply"], "Kính float TQ 5/6 mm cuối 10/2026: 1.069,9 NDT/tấn (−8,2 NDT, −0,8%) – NBS; Viglacera: mảng kính & gương 9T/2026 doanh thu >2.109 tỷ đồng (+49%), Q3 chuyển lỗ sang lãi")
dsrc(c, "Westmetall – LME"); dsrc(c, "LME Weekly 12–16/10")
src(c, "Báo Pháp luật 25/10/2026 – Viglacera Q3", "https://doanhnhan.baophapluat.vn/viglacera-vgc-lai-quy-iii-tang-gap-5-2-lan-mang-kinh-va-guong-chuyen-tu-lo-sang-lai.html", "2026-10-25")
src(c, *NBS)
src(c, "Westmetall – LME 06/11/2026", "https://www.westmetall.com/de/markdaten.php", "2026-11-06")

# Cáp điện – đồng LME lùi → trend flat
c = C["cap-dien"]
c["trend"] = "flat"
c["headline"] = N("Đồng LME hạ nhiệt: giao ngay 13.955 USD/tấn (06/11) so với 14.449 USD/tấn (30/10) và đỉnh ~14.533 USD/tấn (08/09/2026); tồn kho LME 316.675 tấn vẫn cao → xu hướng chuyển đi ngang, giá cáp chững nhưng chưa giảm sâu; Cadivi điều chỉnh bảng giá từ 06/04/2026.")
drop(c["supply"], "Đồng LME giao ngay 14.449")
drop(c["supply"], "Tồn kho đồng LME 273.750")
add(c["supply"], "Tồn kho đồng LME tăng từ 273.750 tấn (23/10) lên 316.675 tấn (06/11); Chile dự kiến sản lượng 2026 −8–9%, nhà máy luyện TQ cắt giảm do thiếu tinh quặng")
add(c["supply"], "Đồng LME giao ngay 13.955 USD/tấn (06/11), giảm từ 14.449 USD/tấn (30/10); đồng điện phân 1# TQ cuối 10/2026 110.175 NDT/tấn (−0,7%) – NBS")
c["rec_detail"] = N("Cáp hạ thế/trung thế: nhà máy VN (giá chiết khấu đại lý 30–40% tham khảo). Ký giá gắn LME đồng + phí gia công; hedge khối lượng lớn. 09/11: đồng lùi khỏi vùng đỉnh → cơ hội chốt giá cáp cho gói Q1/2027 theo công thức LME trung bình tháng, tránh giá cố định dài hạn khi biến động còn lớn.")
dsrc(c, "Westmetall – LME"); dsrc(c, "Trường Giang (cjys.net)")
src(c, *NBS)
src(c, "Westmetall – LME 06/11/2026", "https://www.westmetall.com/de/markdaten.php", "2026-11-06")

# Ống nhựa
c = C["ong-nhua"]
add(c["supply"], "Bình Minh Q3/2026: doanh thu 1.463 tỷ đồng (−4,5%), giá vốn +9,4%, LN trước thuế 399 tỷ (−9,3%) → biên bị ép, khó giảm bảng giá nhưng doanh số yếu → dư địa xin chiết khấu dự án")
add(c["trade"], "Hạt LLDPE TQ cuối 10/2026: 10.201,4 NDT/tấn (+2,0% so với giữa tháng) – NBS")
src(c, *NBS)
src(c, "Báo Pháp luật 19/10/2026 – Bình Minh Q3", "https://doanhnhan.baophapluat.vn/gia-von-tang-cao-loi-nhuan-nhua-binh-minh-bmp-quay-dau-giam-trong-quy-iii-2026.html", "2026-10-19")

# Gạch đá
c = C["gach-da"]
drop(c["trade"], "Canton Fair kỳ 140")
dsrc(c, "Cổng TTĐT Quảng Đông – Canton Fair")
add(c["supply"], "Viglacera 9T/2026: gạch ốp lát doanh thu >3.075 tỷ đồng (+12%); gạch, ngói ~730 tỷ (−15%) (Báo Pháp luật 25/10)")
src(c, "Báo Pháp luật 25/10/2026 – Viglacera Q3", "https://doanhnhan.baophapluat.vn/viglacera-vgc-lai-quy-iii-tang-gap-5-2-lan-mang-kinh-va-guong-chuyen-tu-lo-sang-lai.html", "2026-10-25")

json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("ok", len(d["categories"]))
