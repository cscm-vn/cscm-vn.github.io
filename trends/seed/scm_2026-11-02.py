# Rà soát thứ Hai 02/11/2026: vá trends/data/scm.json hiện hành (tiếp nối scm_2026-10-26.py).
import json, unicodedata
N = lambda s: unicodedata.normalize("NFC", s)
p = "trends/data/scm.json"; d = json.load(open(p, encoding="utf-8"))
d["updated"] = "2026-11-02"
d["freight"]["text"] = N("Cước biển Shanghai → TP.HCM 10/2026: 20GP 645–900 USD, 40HQ 1.190–1.600 USD; → Hải Phòng: 20GP 650–830 USD, 40HQ 1.060–1.560 USD (chưa phí địa phương; TSL cập nhật 15/10, rà soát 02/11 chưa có bảng mới). Nội Á ổn định: SCFI 30/10 tuyến Viễn Đông – Đông Nam Á 1.164 USD/TEU (+18). Tuyến dài đảo chiều giảm: Drewry WCI 29/10 4.429 USD/FEU (−3%); SCFI tổng 3.687,35 (+6,01). Rủi ro phụ phí: Hormuz (Brent 117,64 USD/thùng 30/10).")
d["freight"]["source"] = {"name": "TSL – cước Shanghai → VN (cập nhật 15/10/2026; rà soát 02/11/2026)", "url": "https://tsl.com.vn/gia-cuoc-van-chuyen-tu-shanghai-ve-viet-nam/", "date": "2026-10-15"}
C = {c["id"]: c for c in d["categories"]}
def add(lst, s):
    s = N(s)
    if s not in lst: lst.append(s)
def src(c, name, url, date):
    if all(x["url"] != url for x in c["sources"]): c["sources"].insert(0, dict(name=N(name), url=url, date=date))
# Xi măng – dư cung, clinker TQ xuất khẩu ồ ạt
c = C["xi-mang"]
add(c["trade"], "TQ 9T/2026: xuất khẩu clinker 14,67 triệu tấn (+397,87%), xi măng 5,9 triệu tấn (+34,28%), giá xuất T9 giảm 3,63–7,55% n/n; giá P.O42.5 nội địa Q3 bình quân 251,96 NDT/tấn (−8,59% n/n) (Sina 30/10)")
add(c["supply"], "VN: một số hãng tăng 20.000–50.000 đ/tấn cuối T9 – đầu T10; Hội VLXD: công suất vượt nhu cầu, xuất khẩu chưa phục hồi → giá Q4 neo cao nhưng khó tăng đột biến (Thời báo Ngân hàng 1/11)")
src(c, "Sina Finance 30/10/2026 – xi măng TQ Q3", "https://finance.sina.com.cn/money/future/roll/2026-10-30/doc-iniwyncy2333403.shtml", "2026-10-30")
src(c, "Thời báo Ngân hàng 01/11/2026", "https://thoibaonganhang.vn/vat-lieu-xay-dung-truoc-suc-ep-cao-diem-cuoi-nam-189537.html", "2026-11-01")
# Cát / đá
c = C["cat-da"]
add(c["supply"], "Chênh lệch giá công bố – thực tế: có nơi đá bán 300.000 đ/m³ so với 200.000 đ/m³ ký với CĐT; cao tốc Châu Đốc – Cần Thơ – Sóc Trăng thiếu ~2,5 triệu m³ đá; CV 16346/BXD-KTQLXD (13/10/2026) yêu cầu công bố giá hằng tháng khi biến động")
src(c, "Thời báo Ngân hàng 01/11/2026", "https://thoibaonganhang.vn/vat-lieu-xay-dung-truoc-suc-ep-cao-diem-cuoi-nam-189537.html", "2026-11-01")
# Nhôm
c = C["nhom-kinh"]
add(c["supply"], "Nhôm LME giao ngay 3.114 USD/tấn (30/10, +2,2% so với 26/10); nhôm A00 Trường Giang 23.780 NDT/tấn (30/10)")
src(c, "Westmetall – LME nhôm 2026", "https://www.westmetall.com/en/markdaten.php?action=table&field=LME_Al_cash&year=2026", "2026-10-30")
# Cáp điện – đồng
c = C["cap-dien"]
add(c["supply"], "Đồng LME giao ngay 14.449 USD/tấn (30/10), đi ngang vùng cao; đồng điện phân Trường Giang 110.470 NDT/tấn (30/10, −580)")
src(c, "Trường Giang (cjys.net) – giá giao ngay 30/10/2026", "https://www.cjys.net/price", "2026-10-30")
# TBVS & gạch đá – chỉ số giá Phật Sơn
for cid in ("tbvs", "gach-da"):
    c = C[cid]
    add(c["trade"], "Chỉ số giá gốm sứ Phật Sơn T9/2026: TBVS sứ 68,64 điểm (−9,41% m/m, −7,82% n/n); gạch ốp lát +0,10% m/m; đá nung kết (岩板) −5,64% m/m; gạch ốp tường −4,28% m/m")
    src(c, "CBMinfo 28/10/2026 – chỉ số giá gốm sứ Phật Sơn T9", "https://www.cbminfo.com/BMI/zx/_465657/7462684/index.html", "2026-10-28")
# Tủ bếp / nội thất – An Cường
c = C["tu-bep"]
add(c["supply"], "An Cường Q3/2026 doanh thu 1.201,46 tỷ đồng (+2,2%), hạ kế hoạch doanh thu năm còn 4.811,9 tỷ (−9,2%) → cầu yếu, dư địa đàm phán giá khung 2027")
src(c, "Tin nhanh chứng khoán 29/10/2026 – An Cường Q3", "https://www.tinnhanhchungkhoan.vn/go-an-cuong-acg-lai-42472-ty-dong-trong-9-thang-va-da-trich-lap-1952-ty-dong-khoan-cho-vay-novareal-post400452.html", "2026-10-29")
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("ok", len(d["categories"]))
