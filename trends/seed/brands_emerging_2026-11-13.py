# Khởi tạo box "Thương hiệu mới nổi" (13/11/2026): trends/data/brands.json -> emerging[].
# Mỗi mục: hãng mới vào VN / mới đẩy mạnh kênh dự án / vừa M&A – theo dõi tối đa 90 ngày từ "date", sau đó bỏ hoặc đưa vào danh bạ (seed brands_YYYY-MM-DD.py, R).
import json, unicodedata
N = lambda s: unicodedata.normalize("NFC", s)
p = "trends/data/brands.json"; d = json.load(open(p, encoding="utf-8"))
E = {e["id"]: e for e in d.get("emerging", [])}
def put(**e):
    e = {k: (N(v) if isinstance(v, str) else v) for k, v in e.items()}
    if e["id"] in E: e["first_seen"] = E[e["id"]].get("first_seen", e["first_seen"])
    E[e["id"]] = e
put(id="aeg", name="AEG", origin="Đức", note="Thuộc Electrolux Group", kws=["aeg"], query='"AEG"',
    tax={"ht.thiet-bi-bep": "cao-cap"}, signal="vao-vn", first_seen="2026-08-26", date="2026-08-26",
    why="Ra mắt chính thức tại VN (TP.HCM, 26/08/2026), định vị bếp cao cấp; giai đoạn đầu tập trung kênh dự án – làm việc với chủ đầu tư, kiến trúc sư, nhà phân phối.",
    impl="Thêm vào danh sách mời chào giá gói thiết bị bếp căn hộ cao cấp để tạo áp lực cạnh tranh với Bosch/Siemens; hãng đang cần dự án tham chiếu ở VN nên có thể đề nghị chiết khấu/hỗ trợ mẫu (GIẢ ĐỊNH đàm phán).",
    sources=[{"name": "TheLEADER 26/08/2026 – AEG ra mắt tại VN", "url": "https://theleader.vn/aeg-chinh-thuc-ra-mat-tai-viet-nam-mang-139-nam-di-san-duc-kien-tao-khong-gian-song-cao-cap-d47438.html", "date": "2026-08-26"}])
put(id="haier", name="Haier (mua Ferroli ASEAN)", origin="Trung Quốc", note="Ferroli ASEAN: nhà máy KCN Thạch Thất (Hà Nội)", kws=["haier", "ferroli"], query='"Haier" OR "Ferroli"',
    tax={"mep.hvac": "pho-thong", "ht.thiet-bi-bep": "pho-thong"}, signal="m-a", first_seen="2026-11-05", date="2026-11-05",
    why="Haier mua 100% Ferroli ASEAN (công bố 03/11/2026): Ferroli chiếm ~19% thị phần bình nóng lạnh điện, nhà máy Thạch Thất công suất thiết kế 900.000 bình nóng lạnh, 120.000 thiết bị bếp, 100.000 điều hòa/năm; Haier định dùng VN làm bàn đạp sang Thái Lan, Philippines và mở thêm dòng điều hòa, lọc nước.",
    impl="Hợp đồng khung bình nóng lạnh/bếp Ferroli: kiểm tra điều khoản đổi chủ sở hữu, bảo hành và mã sản phẩm; theo dõi chính sách giá sau tiếp quản để đàm phán đợt mua 2027.",
    sources=[{"name": "VCCI 05/11/2026 – Haier thâu tóm Ferroli ASEAN", "url": "https://vcci.com.vn/tin-tuc/ong-lon-trung-quoc-thau-tom-ferroli-asean-lam-ban-dap-mo-rong-thi-truong-viet-nam", "date": "2026-11-05"}])
d["emerging"] = sorted(E.values(), key=lambda e: e["date"], reverse=True)
C = set(d["cats"]); T = {t["id"] for t in d["tiers"]}; R = {b["id"] for b in d["brands"]}
assert all(c in C and t in T for e in d["emerging"] for c, t in e["tax"].items()) and not (R & set(E))
json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("emerging:", len(d["emerging"]))
