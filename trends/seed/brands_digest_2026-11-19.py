# Tóm tắt tuần thương hiệu (19/11/2026; phủ 13–19/11/2026): trends/data/brands.json
import json, unicodedata
from datetime import date, timedelta
N = lambda s: unicodedata.normalize("NFC", s)
TODAY = "2026-11-19"
p = "trends/data/brands.json"; d = json.load(open(p, encoding="utf-8"))
d["updated"] = TODAY
nz = lambda o: N(o) if isinstance(o, str) else ({k: nz(v) for k, v in o.items()} if isinstance(o, dict) else ([nz(x) for x in o] if isinstance(o, list) else o))
S = lambda name, url, dt: {"name": name, "url": url, "date": dt}
def dg(text, impl, sources):
    return nz({"date": TODAY, "text": text, "impl": impl, "sources": sorted(sources, key=lambda s: s["date"], reverse=True)})
s_ls = S("Korea Herald 17/11/2026 – LS Electric hoàn thành nhà xưởng thứ hai tại Bắc Ninh", "https://www.koreaherald.com/article/10939640", "2026-11-17")
s_cadivi = S("VnEconomy 17/11/2026 – Dây cáp điện CADIVI trong xu hướng công trình xanh", "https://vneconomy.vn/day-cap-dien-cadivi-trong-xu-huong-cong-trinh-xanh.htm", "2026-11-17")
s_haier = S("VCCI 05/11/2026 – Haier thâu tóm Ferroli ASEAN", "https://www.vcci.com.vn/news/ong-lon-trung-quoc-thau-tom-ferroli-asean-lam-ban-dap-mo-rong-thi-truong-viet-nam", "2026-11-05")
B = {b["id"]: b for b in d["brands"]}
B["ls-electric"]["digest"] = dg(
 "Ngày 16/11/2026 LS Electric khánh thành nhà xưởng thứ hai (4 tầng, 7.611 m²) tại KCN Yên Phong, Bắc Ninh, sản xuất RMU, tủ điều khiển pin lưu trữ và ACB; đơn hàng đã nhận đủ chạy hết công suất năm 2027. Doanh thu công ty con tại VN dự kiến tăng từ 83 triệu USD (2022) lên 166 triệu USD (2026), mục tiêu 350 triệu USD năm 2030; hãng nói giữ trên 35% thị phần thiết bị điện hạ thế VN.",
 "Năng lực nội địa tăng giúp rút ngắn lead time ACB/RMU cho tổng thầu; nhưng khi công suất đã kín đơn nên cần chốt tiến độ giao và khóa giá sớm cho gói tủ điện 2027.",
 [s_ls])
B["cadivi"]["digest"] = dg(
 "CADIVI là hãng cáp Việt Nam đầu tiên đạt chứng nhận SGBP cấp cao nhất (Leader) cho dây điện dân dụng không chì (LF) và cáp chậm cháy, ít khói, không halogen (LSHF); chứng nhận giúp tính điểm Green Mark và được LOTUS chấp nhận.",
 "Có thể đưa SGBP vào tiêu chí kỹ thuật cho dự án xin chứng chỉ xanh; dùng làm điểm cộng khi so sánh với cáp nhập/OEM, đồng thời không nên chấp nhận chênh giá chỉ vì chứng nhận (GIẢ ĐỊNH đàm phán).",
 [s_cadivi])
C = d["cats"]
C["mep.tu-dien"]["digest"] = dg(
 "LS Electric mở thêm nhà xưởng ACB/RMU tại Bắc Ninh và nói đã đủ đơn hàng cho cả năm tới – công suất nội địa tăng nhưng nguồn cung ACB/RMU cho các hãng khác sẽ cạnh tranh gay gắt hơn.",
 "Chốt sớm tiến độ và giá cho tủ trung/hạ thế của các dự án khởi công 2027; mời thêm Schneider/ABB/Chint để giữ áp lực giá.",
 [s_ls])
C["mep.cap-dien"]["digest"] = dg(
 "Cadivi đạt SGBP Leader cho cáp xanh (17/11); Taihan xây nhà máy cáp 400 kV tại Đồng Nai (khởi công 03/11, dự kiến vận hành 2027). Trong khi đó Taya (dòng tiền âm) và Cadisun (sai phạm kế toán) vẫn là điểm rủi ro nhà cung cấp.",
 "Ưu tiên hãng tài chính lành mạnh cho gói cáp dự án; thanh toán theo giao hàng với hãng dòng tiền yếu; dùng chứng nhận xanh làm tiêu chí kỹ thuật chứ không phải lý do tăng giá.",
 [s_cadivi] + d["cats"]["mep.cap-dien"]["digest"]["sources"])
# (B) emerging: làm mới Haier
for e in d["emerging"]:
    if e["id"] == "haier":
        e["why"] = N("Haier mua 100% Ferroli ASEAN (công bố 03/11/2026, giá trị không công bố): Ferroli thuộc nhóm 3 hãng bình nóng lạnh điện hàng đầu VN (~19% thị phần); năm 2024 doanh thu thuần giảm 13,44%, lợi nhuận sau thuế giảm 18,63%. Nhà máy Thạch Thất có công suất thiết kế 900.000 bình nóng lạnh, 120.000 thiết bị bếp, 100.000 điều hòa/năm (số thiết kế, không phải sản lượng thực); Haier định dùng VN làm bàn đạp sang Thái Lan, Philippines.")
        e["sources"] = [nz(s_haier)]
        e["date"] = "2026-11-05"
cut90 = (date.fromisoformat(TODAY) - timedelta(days=90)).isoformat()
d["emerging"] = sorted([e for e in d["emerging"] if e["date"] >= cut90], key=lambda e: e["date"], reverse=True)
cut60 = (date.fromisoformat(TODAY) - timedelta(days=60)).isoformat()
for o in list(d["brands"]) + list(d["cats"].values()):
    if o.get("digest") and o["digest"]["date"] < cut60: del o["digest"]
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok")
