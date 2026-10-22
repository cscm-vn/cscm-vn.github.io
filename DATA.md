# Lưu trữ dữ liệu (DATA layout) — schema_version 1

Nguồn chuẩn (canonical) là **văn bản thuần, nối thêm (append-mostly)**, được theo dõi trong git.
`data/prices.db` (SQLite) chỉ là **bản làm việc dựng lại được** — đã `.gitignore`, không commit.

```
data/
  registry/
    datasets.json          # danh mục dataset: schema_version, đường dẫn, khoá, cột
    items.json             # registry mặt hàng: 1 object/dòng {id,status,last_ok,last_try,meta{...}}
    contract_baselines.json   # đơn giá nguyên tắc HĐ tổng thầu (CTD/NTC), ngưỡng, tỷ trọng – nhiều HĐ/phiên bản
    contract_market_map.json  # ánh xạ dòng HĐ (miền|mã) → chuỗi giá thị trường + cách suy diễn + hồ sơ dự báo
  history/
    prices/YYYY-MM.csv     # giá, dạng long: 1 dòng / (item_id, date); lần lấy muộn nhất trong ngày thắng
    runs/YYYY-MM.csv       # nhật ký chạy từng nguồn (fetched_at, source, ok, n, error)
  taxonomy.json            # cây danh mục cho các trang hub
  tthh_snapshot.json       # bản chụp relay từ box (nguồn chặn runner GitHub)
  prices.db                # (gitignored) SQLite dựng từ CSV
```

## prices/YYYY-MM.csv
`date,item_id,region,source,price,price_high,unit,currency,change_pct,fetched_at`
- `date` = ngày giá của nguồn (as_of), phân vùng theo tháng của `date`.
- Khoá duy nhất `(item_id, date)`; file sắp xếp theo `(date, item_id)`; số in dạng ngắn nhất (repr), nên diff git ổn định.
- Cột rỗng = NULL. Thêm cột mới **chỉ ở cuối**, nullable, và tăng `schema_version` trong `store.py`.
- Lấy giá 5 lần/ngày: mỗi lần chỉ thay dòng của ngày hiện tại → git chỉ đổi vài dòng trong file tháng hiện tại.

## Quy trình
- `fetcher.py`: `store.build()` (CSV → SQLite) → lấy giá → `store.dump()` (SQLite → CSV/JSON).
- `app.py`, `forecast/build.py` gọi `store.ensure_db()` (tự dựng lại db nếu thiếu hoặc cũ hơn CSV).
- `python store.py build|dump|check [--db PATH]`.
- `export_static.py` xuất `site/history/<id>.json` gọn (`date`,`price`,`price_high` nếu có) và `site/lich-su-gia.csv` (nút “⬇ Tải CSV lịch sử” trên gia.html).
- Sao lưu: workflow `monthly-backup` (ngày 1 hằng tháng) tạo GitHub Release `backup-YYYY-MM` gồm zip CSV + `prices-*.db.gz` + SHA256SUMS.

## Thêm khu vực / nguồn / mặt hàng mới
Không cần đổi schema: viết hàm `src_xxx()` trả `item(...)` (đặt `region=`, `src=`), thêm vào `SOURCES`
(hoặc `forecast/sources.py: NEW_SOURCES`). `item_id` phải ổn định, nên có tiền tố nguồn + slug khu vực
(vd. `vnmat_xi_mang_..._da_nang`). Tỉnh mới chỉ là giá trị `region` khác.

## Thêm dataset mới (vd. giá trúng thầu, báo giá NCC)
1. Khai báo trong `DATASETS` (`store.py`): `path: history/<tên>/{YYYY-MM}.csv`, `key`, `columns` (long-format: `date,item_id,region,source,...,price,unit,currency` + cột riêng, nullable).
2. Thêm bảng SQLite tương ứng + đoạn dump/build theo mẫu `runs` (đọc/ghi theo tháng, sắp xếp theo khoá).
3. Ghi dữ liệu nhạy cảm (báo giá NCC nội bộ) **không** vào repo public — dùng repo/bucket riêng, cùng định dạng.

## Lên CSDL thật
- SQLite: `python store.py build --db x.db`.
- DuckDB (không cần code): `CREATE TABLE prices AS SELECT * FROM read_csv_auto('data/history/prices/*.csv', header=true);`
- Postgres: `\copy prices FROM PROGRAM 'tail -q -n +2 data/history/prices/*.csv' CSV` (tạo bảng theo `datasets.json`).

## Điều chỉnh giá HĐ tổng thầu (`dieu-chinh.html`)
- `data/registry/contract_baselines.json`: `{schema_version, contracts:[{id, name, version, effective_date, currency, note, bases{CTD,NTC}, source_file, items:[{region: bac|nam, group, code, desc, unit, weight_pct, thr_ctd_pct, thr_ntc_pct, ctd, ntc}]}]}`.
  Ô trống trong HĐ = `null` (không bịa). Nhiều HĐ: thêm `id` khác; sửa giá: nhập `version` mới (bản có `effective_date` ≤ hôm nay và version lớn nhất được dùng).
  Nhập từ Excel/TSV: `python dieu_chinh/import_tsv.py FILE.tsv --id tong-thau-2026 --name "…" --version YYYY-MM-DD --effective YYYY-MM-DD`.
- `data/registry/contract_market_map.json`: mỗi khóa `miền|mã` → `method` (`median` | `ratio` | `interp` | `norm` | `none`), `series[{id, use: price|mid|high, factor, vat_incl, role: check}]`, `quality` (A/B/C), `note` (giải thích hiển thị trên trang).
- `dieu_chinh/build.py --site site` (chạy sau forecast, trước trends/build) → `site/data/dieu-chinh.json`, `site/data/dieu-chinh-summary.json` (thanh điều hướng + trang chủ), `site/dieu-chinh.csv`, `site/dieu-chinh.xlsx`.
- Lưu ý: push chỉ sửa `data/registry/**` không kích hoạt workflow (paths-ignore) → trang cập nhật ở lần chạy theo lịch kế tiếp hoặc chạy tay `workflow_dispatch`.
