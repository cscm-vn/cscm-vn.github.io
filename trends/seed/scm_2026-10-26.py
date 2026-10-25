# Rà soát thứ Hai 26/10/2026: vá trends/data/scm.json hiện hành (không chạy lại bản 10-22 vì scm.json đã được chỉnh tay sau đó).
import json, unicodedata
N = lambda s: unicodedata.normalize("NFC", s)
p = "trends/data/scm.json"; d = json.load(open(p, encoding="utf-8"))
d["updated"] = "2026-10-26"
d["freight"]["text"] = N("Cước biển Shanghai → TP.HCM 10/2026: 20GP 645–900 USD, 40HQ 1.190–1.600 USD; → Hải Phòng: 20GP 650–830 USD, 40HQ 1.060–1.560 USD (chưa phí địa phương; TSL cập nhật 15/10, rà soát 26/10 không đổi). Tuyến dài tăng: Drewry WCI 22/10 4.585 USD/FEU (+2%, cao nhất 15 tuần); SCFI 23/10 3.681,34 (+1,76).")
d["freight"]["source"] = {"name": "TSL – cước Shanghai → VN (cập nhật 15/10/2026)", "url": "https://tsl.com.vn/gia-cuoc-van-chuyen-tu-shanghai-ve-viet-nam/", "date": "2026-10-15"}
C = {c["id"]: c for c in d["categories"]}
def add(lst, s):
    s = N(s)
    if s not in lst: lst.append(s)
def src(c, name, url, date):
    if all(x["url"] != url for x in c["sources"]): c["sources"].insert(0, dict(name=N(name), url=url, date=date))
# Thép
c = C["thep"]
add(c["demand"], "TQ: tiêu thụ biểu kiến thép cây 201,03 vạn tấn/tuần – thấp nhất cùng kỳ 4 năm; giá Φ20 bình quân 3.311 NDT/tấn (Mysteel 24/10)")
src(c, "Mysteel 24/10/2026 – thép cây TQ", "https://news.mysteel.com/a/26102416/3100BAA241FF9640.html", "2026-10-24")
# Nhôm – kính
c = C["nhom-kinh"]
c["headline"] = N("Kính float TQ yếu (~1.058–1.060 NDT/tấn giữa 10/2026); nhôm LME nhích lên 3.043 USD/tấn (giao ngay 23/10, tồn kho SHFE giảm 8 tuần); nhôm định hình TQ chịu CBPG 2,85–35,58% đến 2029.")
add(c["supply"], "Nhôm LME giao ngay 3.043 USD/tấn, 3 tháng 3.018 USD/tấn (23/10); tồn kho LME 235.800 tấn")
src(c, "Westmetall – LME 23/10/2026", "https://www.westmetall.com/en/markdaten.php/en/leistungen/neumetalle.html", "2026-10-23")
# Cáp điện – đồng
c = C["cap-dien"]
c["headline"] = N("Đồng LME vẫn ở vùng cao 14.415 USD/tấn (giao ngay 23/10) sau đỉnh ~14.533 USD/tấn (08/09/2026); tồn kho LME tăng ~1/5 trong tuần → biến động mạnh, giá cáp chưa có dư địa giảm; Cadivi điều chỉnh bảng giá từ 06/04/2026.")
add(c["supply"], "Tồn kho đồng LME 273.750 tấn (23/10), tăng ~1/5 trong tuần; Chile dự kiến sản lượng 2026 −8–9%, nhà máy luyện TQ cắt giảm do thiếu tinh quặng")
src(c, "Westmetall – LME đồng 2026", "https://www.westmetall.com/en/markdaten.php?action=table&field=LME_Cu_cash&year=2026", "2026-10-23")
src(c, "AEGIS/Bloomberg 23/10/2026", "https://instanext.com/insights/metals/daily-first-look/2026-10-23", "2026-10-23")
# Gạch đá & TBVS – nguồn TQ
c = C["gach-da"]
add(c["trade"], "Gạch ốp lát TQ: đơn giá xuất khẩu 9T/2026 2.607 NDT/tấn (−15,2% n/n), lượng 9,77 triệu tấn (−1,4%) – áp lực giá chào FOB giảm")
add(c["trade"], "Canton Fair kỳ 140 GĐ2 (23–27/10, Quảng Châu): VLXD & trang trí khu B 11.2–13.2, TBVS khu B 9.1–11.1")
src(c, "jc68 – xuất khẩu gốm sứ XD TQ 9T/2026", "https://www.jc68.com/news/show-25451.html", "2026-10-24")
src(c, "Cổng TTĐT Quảng Đông – Canton Fair GĐ2 23/10/2026", "https://www.gd.gov.cn/gdywdt/ydylygd/content/post_4969751.html", "2026-10-23")
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("ok", len(d["categories"]))
