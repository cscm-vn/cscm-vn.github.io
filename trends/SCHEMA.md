# Hub dữ liệu Xu hướng & Thị trường – schema & quy trình cập nhật hằng ngày

## Tệp
| Tệp | Nội dung | Ai ghi |
|---|---|---|
| `data/taxonomy.json` | Cây danh mục dùng chung (cấp 1 → cấp 2, id dạng `xd.cot-thep`) + quy tắc tự gán (`match.cats/ids/kw`). Mọi trang (Giá, Dự báo, Xu hướng, Thị trường) đọc tệp này. | người |
| `trends/data/trends.json` | Xu hướng & cơ hội (có lịch sử, không xóa) | `trends/merge.py` |
| `trends/data/market.json` | Tin thị trường biên tập | `trends/merge.py` |
| `trends/data/feed.json` | Tin tự động RSS/Google News (cuộn 45 ngày) | `trends/feeds.py` (GitHub Actions) |
| `site/data/hub.json` | Sinh khi build: giá gắn danh mục, MoM/YoY, chuỗi tháng, so sánh Hà Nội–TP.HCM, digest tháng | `trends/build.py` |

## Mục xu hướng (`type: "trend"`)
```json
{"type":"trend","title":"…","tax":["ht.tbvs","tt.trung-quoc"],"region":"Trung Quốc","date":"2026-10-21",
 "summary":"Tóm tắt tiếng Việt, chỉ dữ kiện có trong nguồn","why":"Ý nghĩa với Masterise (chi phí/chất lượng/rủi ro)",
 "impact":{"kind":"cost|quality|risk","level":"cao|trung bình|thấp","estimate":"ước tính tác động"},
 "sources":[{"name":"Tên nguồn","url":"https://…"}],
 "scores":{"novelty":1-5,"cost_saving":1-5,"quality":1-5,"applicability":1-5,"supplier":1-5},"tags":["…"]}
```
`score` (/100) = (0.15·novelty + 0.30·cost_saving + 0.20·quality + 0.25·applicability + 0.10·supplier)/5·100 – merge.py tự tính; `category`, `l1`, `id`, `added`, `updated` cũng tự điền.

## Mục thị trường (`type: "market"`)
```json
{"type":"market","title":"…","segment":"Căn hộ|Thấp tầng|Chính sách|Tài chính & lãi suất|Nhà thầu|Doanh nghiệp|Vật liệu|Thế giới",
 "region":"Hà Nội|TP.HCM|Toàn quốc|Trung Quốc|Toàn cầu|Châu Âu","date":"YYYY-MM-DD","summary":"…","takeaway":"(tùy chọn) hàm ý",
 "tax":["tt.bds"],"sources":[{"name":"…","url":"https://…"}]}
```

## Chống trùng
Trùng nếu **URL nguồn đầu tiên** (chuẩn hóa, bỏ http/www/query) hoặc **tiêu đề chuẩn hóa** (không dấu) đã có → cập nhật mục cũ, gộp thêm nguồn mới, giữ `added`. Tin RSS không bao giờ ghi đè mục biên tập.

## Quy trình hằng ngày (trợ lý)
```bash
cd /workspace/gia-vat-tu-repo && git pull --rebase   # remote: github.com/cscm-vn/cscm-vn.github.io · site: https://cscm-vn.github.io/
# 1) nghiên cứu web, ghi các mục mới vào trends/seed/YYYY-MM-DD.json  (list hoặc {"trends":[…],"market":[…]})
python3 trends/merge.py trends/seed/2026-10-22.json      # báo +mới / cập nhật / tổng; lỗi nếu thiếu nguồn hoặc tax sai
python3 export_static.py && python3 trends/build.py       # (tùy chọn) xem trước cục bộ
python3 trends/test_ui.py http://127.0.0.1:PORT/          # (tùy chọn) kiểm thử giao diện, ảnh vào screenshots/
git add trends data/taxonomy.json && git commit -m "trends: cập nhật 2026-10-22" && git pull --rebase && git push
# push kích hoạt workflow update-prices → build & deploy GitHub Pages (~1–2 phút)
```
## Hợp đồng với trang Dự báo
`forecast/build.py` gắn `tax` (id cấp 2) cho mỗi chuỗi dự báo trong `site/forecast.json`; trang Danh mục & Mặt hàng hiển thị dự báo theo `tax`. Thêm danh mục mới: sửa `data/taxonomy.json` (không đổi id cũ).

## v3 – Nhà thầu & Chủ đầu tư (trong `market.json`)
Thêm vào mục `market`: `"org":"Coteccons"`, `"org_type":"contractor|developer"`, `"mseg":"hang-sang|cao-cap|trung-cap|noxh|thap-tang|nghi-duong|van-phong"` (tùy chọn).
Tên `org` phải trùng tên trong `ORGS` của `trends/feeds.py` để bộ lọc gộp tin biên tập + tin RSS. Cùng một URL có thể dùng cho 2 đơn vị khác nhau (merge.py giữ cả hai nếu `org` và tiêu đề khác nhau).
Thêm đơn vị theo dõi mới: thêm 1 dòng vào `ORGS` (tên, loại, truy vấn Google News, từ khóa không dấu khớp tiêu đề).

## v3 – SCM (`trends/data/scm.json`, sinh từ `trends/seed/scm_YYYY-MM-DD.py`)
Mỗi nhóm: `id, name, tax[], signal (du-cung|can-bang|khan-hiem|chua-du), trend (up|down|flat), headline, supply[], demand[], trade[], rec, rec_detail, clusters[{name,where,examples}], risks[], levers[], timing, calc{unit,fob,qty,cont,duty,ad,vat,logi,note,vn,vn_note}|null, sources[{name,url,date}]`.
Quy tắc: mọi số liệu phải có trong nguồn ghi kèm; FOB/giả định ghi chữ **GIẢ ĐỊNH** trong `calc.note`. Cập nhật **hằng tháng** hoặc khi có biến động lớn (thuế CBPG mới, giá LME, báo cáo VSA/VNCA). Cước biển: `freight` (cập nhật hằng tháng).

## v3 – Phân khúc (`trends/data/segments.json`, sinh từ `trends/seed/segments_YYYYQn.py`)
7 phân khúc × {hn, hcm}: `price, trend, supply, absorption, inventory, projects, sources[]` + `spec, cost{structure,fitout,sources}, implications`. Cập nhật **hằng quý** khi CBRE/Savills/DKRA/VARS/NAI công bố (thường giữa tháng đầu quý sau). Dòng ước tính phải có chữ **ƯỚC TÍNH**.

## Quy trình hằng ngày – bổ sung v3
1. Tin nhà thầu/CĐT: thêm mục `market` có `org`/`org_type` vào seed ngày (trúng thầu, backlog, KQKD, mở bán, giá/m², tiêu chuẩn bàn giao, NCC được chỉ định).
2. Nếu có thay đổi cung cầu đáng kể → sửa `trends/seed/scm_*.py`, chạy lại → commit `trends/data/scm.json`.
3. Kiểm thử: `python3 trends/test_v3.py http://127.0.0.1:PORT/` (360/390/768/1366, ảnh `screenshots/v3_*.png`).

## Hợp đồng & Pháp lý (`hop-dong.html`)
| Tệp | Nội dung | Ai ghi |
|---|---|---|
| `trends/data/legal.json` | Văn bản pháp luật (số hiệu, ban hành, hiệu lực, tóm tắt, tác động HĐ, nguồn) | `trends/hopdong/build_data.py` (biên tập) |
| `trends/data/fidic.json` | Điều khoản FIDIC 2017 tóm tắt + so sánh quy định VN (không trích nguyên văn) | như trên |
| `trends/data/trade-remedies.json` | Vụ việc PVTM: mã vụ, sản phẩm, xuất xứ, QĐ, ngày, mức thuế, mã HS, `status` = dang-ap-dung / dang-ra-soat / dang-dieu-tra / da-ket-thuc | như trên |
| `trends/data/disputes.json` | Tranh chấp & án lệ: các bên, vấn đề, kết quả, bài học | như trên |
| `trends/data/quiz.json` | Ngân hàng câu hỏi (≥60), `answer` = chỉ số đáp án, `sources` | như trên |
| `trends/data/checklist.json` | Checklist rà soát HĐ | như trên |
| `trends/data/legal-feed.json` | Tin quét tự động, `reviewed:false` – KHÔNG phải nội dung biên tập | `trends/legal_feed.py` (GitHub Actions) |

Mọi tệp có `schema_version`, `reviewed` (ngày biên tập gần nhất). Quy tắc: mỗi mục phải có `sources` là URL đã mở và kiểm chứng; không kiểm chứng được thì bỏ. Thêm nguồn quét: sửa `Q`/`OFFICIAL` trong `legal_feed.py`.
QA: `python trends/hopdong/qa.py <BASE_URL> [--shots]` (tràn ngang mọi trang ở 360–1920px, hỏi đáp, xoay vòng câu hỏi).
