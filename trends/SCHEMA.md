# Hub dữ liệu Xu hướng & Thị trường – schema & quy trình cập nhật hằng ngày

## Tệp
| Tệp | Nội dung | Ai ghi |
|---|---|---|
| `data/taxonomy.json` | Cây danh mục dùng chung (cấp 1 → cấp 2, id dạng `xd.cot-thep`) + quy tắc tự gán (`match.cats/ids/kw`). Mọi trang (Giá, Dự báo, Xu hướng, Thị trường) đọc tệp này. | người |
| `trends/data/trends.json` | Xu hướng & cơ hội (có lịch sử, không xóa) | `trends/merge.py` |
| `trends/data/market.json` | Tin thị trường biên tập | `trends/merge.py` |
| `trends/data/feed.json` | Tin tự động RSS/Google News (cuộn 45 ngày), gồm `site:` zh-CN: zhulong.com, co188.com, goods.jc001.cn, home.163.com | `trends/feeds.py` (GitHub Actions) |
| `trends/data/orgs.json` | Đơn vị theo dõi (nhà thầu, CĐT) — truy vấn Google News vi + `query_zh` | người |
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
{"type":"market","title":"…","segment":"Căn hộ|Thấp tầng|Chính sách|Tài chính & lãi suất|Nhà thầu|Doanh nghiệp|Vật liệu|Thế giới|Nhân công",
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
Tên `org` phải trùng `name` trong `trends/data/orgs.json` (feeds.py nạp thành `ORGS`) để bộ lọc gộp tin biên tập + tin RSS. Cùng một URL có thể dùng cho 2 đơn vị khác nhau (merge.py giữ cả hai nếu `org` và tiêu đề khác nhau).
Thêm đơn vị theo dõi mới: thêm một object vào `orgs.json` (`name`, `type`, `query`, `kws`; `query_zh` nếu cần Google News zh-CN; `aliases` gồm tên tiếng Trung khi có). Không điền MST hay BCTC nếu chưa đối chiếu nguồn. Nguồn báo Trung Quốc thêm vào `CN_SITES` trong `trends/feeds.py` (cùng dạng `site:domain … when:Nd` + `zh-CN`/`CN`/`zh-Hans`). Mỗi lần fetch bọc try/except — nguồn lỗi không làm fail cả feed.

## v3 – SCM (`trends/data/scm.json`, sinh từ `trends/seed/scm_YYYY-MM-DD.py`)
Mỗi nhóm: `id, name, tax[], signal (du-cung|can-bang|khan-hiem|chua-du), trend (up|down|flat), headline, supply[], demand[], trade[], rec, rec_detail, clusters[{name,where,examples}], risks[], levers[], timing, calc{unit,fob,qty,cont,duty,ad,vat,logi,note,vn,vn_note}|null, sources[{name,url,date}]`.
Quy tắc: mọi số liệu phải có trong nguồn ghi kèm; FOB/giả định ghi chữ **GIẢ ĐỊNH** trong `calc.note`. Cập nhật **hằng tuần – sáng thứ Hai** (lịch tự động "CSCM weekly SCM supply-demand review"; vá `scm.json` bằng script `trends/seed/scm_YYYY-MM-DD.py`, xem mẫu `scm_2026-11-02.py`) và ngay khi có biến động lớn (thuế CBPG mới, giá LME, báo cáo VSA/VNCA). Cước biển: `freight` (rà soát hằng tuần).

## v3 – Thương hiệu (`trends/data/brands.json` + `trends/data/brand-feed.json`; tab "Thương hiệu" ở `danh-muc.html`)
`brands.json`: `tiers[{id: hang-sang|cao-cap|trung-cap|pho-thong, name, use}]`, `cats{<tax cấp 2>: {ctx, digest?}}`, `brands[{id, name, origin, note, kws[], query, tax{<tax cấp 2>: <tier>}, digest?}]`.
- Danh bạ (hãng, phân khúc, kws, query) sinh bằng `trends/seed/brands_YYYY-MM-DD.py` (script giữ nguyên `digest` đã có). Thêm hãng/danh mục: sửa danh sách `R`/`CTX` trong script mới nhất rồi chạy lại. `kws` không dấu, khớp nguyên từ trong tiêu đề; tên dễ trùng (Trần Phú, Tiền Phong, TOA…) dùng cụm có ngữ cảnh.
- Phân khúc = định vị giá phổ biến tại VN (biên tập, tham khảo); một hãng có thể khác phân khúc theo danh mục.
- `digest` (biên tập, lịch tuần thứ Năm "CSCM weekly brand digest"): `{date, text, impl, sources[{name,url,date}]}` cho hãng và cho `cats[c]`. Quy tắc như SCM: mọi số liệu có trong nguồn đã mở; viết lại bằng lời mình; vá bằng `trends/seed/brands_digest_YYYY-MM-DD.py`; bỏ digest > 60 ngày không còn đúng.
- `emerging[]` – box "Thương hiệu mới nổi" (lịch tuần): `{id, name, origin, note, kws[], query, tax{<tax>: <tier>}, signal: vao-vn|mo-rong|m-a|du-an|san-pham, why, impl, first_seen, date, sources[]}`. Tiêu chí: hãng mới vào VN, mới đẩy kênh dự án/chủ đầu tư, M&A, nhà máy/nhà phân phối mới, hoặc tăng trưởng nhanh – có nguồn trong ~90 ngày. `id` không trùng danh bạ; brand_feed.py cũng lấy tin cho các hãng này. Bỏ mục khi `date` > 90 ngày không có tin mới; hãng đã thành lựa chọn thường xuyên → chuyển vào `R` của seed danh bạ và xoá khỏi `emerging`. Vá bằng `trends/seed/brands_digest_YYYY-MM-DD.py` (hoặc `brands_emerging_YYYY-MM-DD.py`).
- `brand-feed.json` (tự động, `trends/brand_feed.py` trong update.yml, 5 lần/ngày): Google News vi/VN, mỗi danh mục gộp ≤6 hãng/truy vấn + `ctx`; chỉ giữ tin có tiêu đề nêu hãng của danh mục; cuộn 90 ngày; `items[{id,title,url,source,date,brands[],tax[]}]`. CHƯA biên tập.

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

## v4 – Nhân công xây dựng (`tt.nhan-cong`)
- Nút cấp 2 `tt.nhan-cong` ("Nhân công & lao động xây dựng") dưới "Vĩ mô & thương mại" trong `data/taxonomy.json` (không có `match`, nên không gán theo từ khóa OR).
- Tin biên tập: `market` với `segment: "Nhân công"`, `tax: ["tt.nhan-cong","tt.bds"]`, `takeaway` = 1 dòng ảnh hưởng đến mua sắm/đấu thầu; số liệu chỉ trích đúng như trong nguồn.
- Tin tự động: `feeds.py` gắn `tt.nhan-cong` (đứng đầu `tax`) khi khớp **từ nhân công** (`LABOR`) **và** ngữ cảnh xây dựng (`LABOR_CTX`), khớp nguyên từ, loại `LABOR_NOT` (xây dựng Đảng, nông thôn mới…). Điểm cộng `LKW` chỉ áp cho tin đã khớp, nên điểm các tin khác không đổi.


## Mới hôm nay & nhãn MỚI (`trends/fresh.py` → `data/fresh.json`)
- CI chạy `trends/fresh.py` sau feeds/policy/highlights, trước `trends/build.py`. Xuất tin (trends, market, RSS feed, policy-feed) và giá đổi trong ~30 giờ, mỗi mục có `ts`.
- `ts` tin = lần đầu site thấy mục đó, lưu ở `trends/data/fresh_seen.json` (CI commit; không sửa tay; `~` = giờ ước tính lúc khởi tạo). policy-feed dùng `found`. Chỉ tính tin có ngày/`added` là hôm nay hoặc hôm qua (giờ VN).
- `ts` giá = `fetched_at` của dòng lịch sử gần nhất có giá khác dòng trước (bỏ mã đang `stale`).
- Trình duyệt (`hub-common.js`: `HUB.fresh`, `HUB.decorate`, `HUB.freshStrip`) lọc lại theo giờ người xem: nhãn MỚI tự mất sau 24 giờ dù site chưa build lại. Nhãn gắn theo URL nguồn, `xu-huong.html?id=`, `thi-truong.html?id=`, `mat-hang.html?id=`, `button.hist[data-id]` (bảng giá) và đếm "MỚI n" trên tiêu đề nhóm master data. Bỏ qua vùng có class `newtag-skip`.

## Đứng giá (`flat_*` trong `site/data/hub.json`, `trends/build.py: flat_info`)
- Mỗi mã: `flat_since` = ngày bắt đầu chuỗi giá (và giá cao) không đổi tới điểm mới nhất, `flat_days`, `flat_open` (chưa đổi lần nào từ khi bắt đầu theo dõi). Chỉ ghi khi `flat_days >= 14`.
- `frozen` = nghi nguồn chưa cập nhật: hàng hóa/tỷ giá ≥10 ngày; thép (`vnsteel*`), cáp (`cable_*`) ≥21 ngày; bảng giá NCC khác ≥45 ngày; công bố Sở XD (định kỳ) không xét.
- `frozen_sources[]` gom theo nguồn -> banner cảnh báo ở gia.html; nhãn "⚠ đứng giá từ dd/mm" / "không đổi từ dd/mm" ở bảng giá, danh mục, mặt hàng, ô KPI trang chủ (`HUB.flat`).
- Lưu ý: fetcher gán `as_of` = ngày tải cho nguồn trang web tĩnh, nên "Ngày giá" không cho biết NCC đổi giá lúc nào – dùng `flat_since`.

## Nguồn chính thức thay nguồn web đứng giá (Sở XD TP.HCM, `hcm_sxd.py`)
- Ngoài xi măng/cát/đá/gạch, `hcm_sxd.py` đọc thêm phụ lục **thép xây dựng, vật tư ngành điện (cáp CADIVI), bê tông thương phẩm, vữa** (nhận diện theo tiêu đề trang 1) → mã `sxd_hcm_thep_*`, `sxd_hcm_cap_*`, `sxd_hcm_rmc_m*`, `sxd_hcm_vua_*`; giá NSX/NCC kê khai, chưa VAT, đơn vị VND/kg (thép quy từ đ/tấn), VND/m, VND/m³, VND/bao. Lưu trong `data/hcm_sxd/YYYY-MM.json` khóa `series`; lịch sử các tháng trước nạp bù qua `backfill`.
- Bê tông: khoảng thấp–cao giữa các NCC theo mác; cáp: danh sách mã đại diện `CABLE_KEEP`. Thép: theo nhà máy × sản phẩm (cuộn/thanh vằn, dải đường kính) × mác.
- Các nguồn web cũ (steelonline, đại lý CADIVI, web NCC bê tông) vẫn giữ nhưng có nhãn đứng giá; ô KPI trang chủ dùng nguồn Sở XD cho phía TP.HCM.
- Thăm dò nguồn mới: workflow tay `probe-sources` (`tools/probe_sources.py`: `sxd` liệt kê phụ lục, `rows` in dòng, `hcm` chạy thử, `web` tải thử URL trong `tools/probe_urls.txt`).
