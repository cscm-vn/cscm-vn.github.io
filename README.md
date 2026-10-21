# Bảng giá kim loại & vật liệu xây dựng (Thế giới + Việt Nam)

Dashboard tiếng Việt cho bộ phận Mua sắm/Đấu thầu: giá kim loại thế giới (LME/COMEX/SHFE), thép xây dựng VN theo hãng & miền,
xi măng, cát, đá, gạch, vàng SJC, tỷ giá Vietcombank. Có lọc/tìm kiếm (không dấu), quy đổi VND, % thay đổi, biểu đồ lịch sử, xuất CSV/Excel,
cờ "dữ liệu cũ" khi nguồn lỗi (giữ giá tốt gần nhất – không bao giờ tự bịa giá).

## Cấu trúc
- `fetcher.py` – lấy giá từ mọi nguồn → `data/prices.db` (SQLite: `items` = giá mới nhất + trạng thái, `obs` = lịch sử, `runs` = log từng nguồn).
- `app.py` – Flask/gunicorn, cổng 8080: `/`, `/api/prices`, `/api/history/<id>`, `/api/sources`, `/api/export.csv|xlsx?group=&q=`, `/healthz`.
- `static/index.html` – giao diện (Chart.js đóng gói sẵn, không phụ thuộc CDN). Tự tải lại mỗi 15 phút.
- `export_static.py` – xuất bản tĩnh vào `site/` (chạy được trên GitHub Pages/Netlify; UI tự nhận chế độ tĩnh).
- `hanoi_sxd_q3_2026.json` – giá công bố Quý III/2026 của Sở XD Hà Nội (nhập tay từ PDF, cần cập nhật mỗi quý).
- `run_fetch.sh` (cron), `watchdog.sh` (giữ server sống), `start_tunnel.sh` (Cloudflare quick tunnel, tùy chọn).

## Nguồn dữ liệu
| Nhóm | Nguồn | Tần suất gốc |
|---|---|---|
| Tỷ giá USD/EUR/CNY | Vietcombank XML (portal.vietcombank.com.vn) | trong ngày |
| LME Cu/Al/Zn/Ni/Pb/Sn (cash, 3M) + LBMA gold | westmetall.com (bảng giá LME chính thức, có lịch sử ~90 phiên) | ngày (T-1) |
| COMEX Cu/Al/Gold/Silver, CME HRC, SGX iron ore | Yahoo Finance qua `yfinance` (HG=F, ALI=F, GC=F, SI=F, HRC=F, TIO=F) | ngày, trễ ~10–20' |
| SHFE rebar (CNY/t), HRC, quặng sắt, phế liệu, than cốc, kim loại màu | tradingeconomics.com/commodities (trang công khai) | gần thời gian thực |
| Vàng SJC | giavang.org (chính), webgia.com (đối chiếu) | trong ngày |
| Thép xây dựng VN (Hòa Phát, Việt Ý, Việt Đức, Kyoei, Thái Nguyên, VAS, Pomina, Việt Sing, TungHo, Miền Nam; Bắc/Trung/Nam) | steelonline.vn/price-list | ngày |
| Xi măng, cát, đá, gạch (TP.HCM) | thitruonghanghoa.com (tổng hợp công bố giá Sở XD) | tháng |
| Xi măng, cát, đá, thép – Hà Nội | Sở XD Hà Nội, công bố giá Quý III/2026 (dữ liệu tĩnh) | quý |

## Lịch cập nhật (cron trên box, giờ VN)
- `5 */3 * * *` → 00:05, 03:05, 06:05, … 21:05 + `35 7 * * *` (chạy bổ sung buổi sáng).
- `*/5 * * * *` watchdog: tự khởi động lại web server nếu chết. `@reboot`: khởi động server + fetch.

## Chạy thủ công
```bash
pip install -r requirements.txt
python3 fetcher.py                      # lấy giá (SIMULATE_FAIL="steelonline.vn" để thử tình huống nguồn lỗi)
gunicorn -w 2 -b 0.0.0.0:8080 app:app   # http://localhost:8080
./start_tunnel.sh                       # URL trycloudflare.com ngẫu nhiên, ĐỔI mỗi lần khởi động lại
```

## Truy cập công khai / hosting ổn định
Quick tunnel Cloudflare **không chạy được trên box này** (mạng chặn cổng 7844 TCP/UDP; SSH tunnel cũng bị chặn). Các lựa chọn ổn định:
1. **GitHub Pages + GitHub Actions (miễn phí, khuyến nghị)**: tạo repo (có thể private với GitHub Team/Enterprise, Pages private cần gói trả phí; public thì ai có link đều xem được),
   đẩy thư mục này lên, bật Settings → Pages → Source: GitHub Actions.
   Workflow chạy 5 lần/ngày, commit `data/prices.db` (giữ lịch sử) và deploy `site/`. Cần: tài khoản GitHub + bật Actions. Lưu ý IP của GitHub runner có thể bị một số site (TE/Yahoo) chặn → khi đó dòng tương ứng hiện "dữ liệu cũ".
2. **Render / Railway / Fly.io** (chạy nguyên app Flask + cron job): cần tài khoản, ổ đĩa persistent cho `data/prices.db` (gói free của Render không có disk → dùng bản tĩnh hoặc gói trả phí ~7 USD/tháng).
3. **Cloudflare Tunnel có tài khoản (named tunnel)** trên một máy/VM nội bộ có mở cổng 7844 ra ngoài → URL cố định trên domain công ty, có thể gắn Cloudflare Access (đăng nhập email @masterisehomes.com).
4. **Máy chủ nội bộ Masterise** (VM Linux bất kỳ): chạy y hệt box này (gunicorn + cron), mở cổng nội bộ – an toàn nhất về dữ liệu.

## Hạn chế
- Giá VN trên web là giá tham khảo đại lý/tổng hợp, chưa VAT/vận chuyển; không thay thế báo giá chính thức hoặc công bố giá có hiệu lực pháp lý.
- Xi măng/cát/đá/gạch chỉ cập nhật theo tháng (TP.HCM) và theo quý (Hà Nội, nhập tay) – có nhãn "định kỳ".
- Scraper phụ thuộc cấu trúc HTML của từng site; nếu site đổi giao diện, nguồn đó báo "Lỗi" trong bảng trạng thái và giá giữ ở lần tốt gần nhất.
- Lịch sử: LME (~90 phiên) và Yahoo (~3 tháng) được nạp sẵn; các nguồn khác tích lũy từ 21/10/2026.
- HRC (CME) tính theo short ton; đã quy đổi sang VND/tấn mét. Đồng COMEX USD/lb → VND/tấn. Vàng USD/oz → VND/lượng (37,5 g).

## 📈 Dự báo & Chiến lược (`forecast/`, trang `forecast.html`)
- `forecast/sources.py` – nguồn giá giao ngay bổ sung, đã cắm vào `fetcher.py` (`SOURCES += NEW_SOURCES`): bê tông tươi M250/M300 Hà Nội (betonghanoi.com.vn, betongtuoichem.com) & TP.HCM (betongdvc.com); PE/PVC/PP (Trading Economics, CNY/t); ống HDPE PE100 Tiền Phong (ongnuoctienphong.vn).
- `forecast/build.py` – chạy SAU `export_static.py`: `python forecast/build.py --site site` → `site/forecast.json` + `site/forecast.html`.
  Lịch sử tháng: World Bank Pink Sheet + Yahoo Finance (HG, ALI, TIO, HRC, BUS, BZ, MTF, VND=X, DXY) + đường cong futures (LME 3M, COMEX, ICE Brent).
  Mô hình: ensemble RW/ETS/ARIMA/ARIMAX + futures; pass-through cho thép VN; mô hình chi phí cấu thành cho xi măng/cát/đá/bê tông/ống nhựa; chỉ số chi phí đầu vào MEP.
  Backtest rolling-origin (60 tháng) → MAPE hiển thị trên trang.
- `forecast/drivers.json` – yếu tố vĩ mô/địa chính trị (link nguồn, chiều tác động, % điều chỉnh kịch bản). **Rà soát thủ công mỗi tuần.**
- `forecast/test_ui.py` – kiểm thử headless (Playwright) + chụp màn hình.
- Workflow: bước "Build forecasts" chạy sau export, `continue-on-error` (lỗi dự báo không chặn deploy bảng giá). Pink Sheet cache 7 ngày trong `forecast/raw/` (không commit).
- Hạn chế: thép VN/xi măng/cát/đá/bê tông chưa có lịch sử dài → hệ số pass-through/tỷ trọng chi phí là giả định, độ tin cậy thấp; ước lượng lại khi `data/prices.db` tích lũy ≥ 24 tháng.

## Hub hằng ngày (Trang chủ · Danh mục · Xu hướng & Cơ hội · Thị trường · Diễn biến tháng/năm)
- Trang chủ `index.html` (bảng giá cũ chuyển sang `gia.html`, dự báo `forecast.html`), cây danh mục dùng chung `data/taxonomy.json`.
- Mã nguồn & dữ liệu: `trends/` – `merge.py` (gộp mục mới, chống trùng), `feeds.py` (RSS/Google News miễn phí, chạy trong Actions), `build.py` (sinh trang + `site/data/hub.json`), `test_ui.py` (kiểm thử headless). Schema & quy trình: `trends/SCHEMA.md`.

## Hướng dẫn sử dụng
Xem trang `huong-dan.html` trên site (mục "Hướng dẫn" trên thanh điều hướng).
