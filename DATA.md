# Lưu trữ dữ liệu (DATA layout) — schema_version 1

Nguồn chuẩn (canonical) là **văn bản thuần, nối thêm (append-mostly)**, được theo dõi trong git.
`data/prices.db` (SQLite) chỉ là **bản làm việc dựng lại được** — đã `.gitignore`, không commit.

```
data/
  registry/
    datasets.json          # danh mục dataset: schema_version, đường dẫn, khoá, cột
    items.json             # registry mặt hàng: 1 object/dòng {id,status,last_ok,last_try,meta{...}}
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
