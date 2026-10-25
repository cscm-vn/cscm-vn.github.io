#!/bin/bash
# Chạy được từ bất kỳ clone nào: tự chuyển vào thư mục chứa script (kể cả khi cron gọi bằng đường dẫn tuyệt đối).
cd "$(dirname "$(readlink -f "$0")")" || exit 1
mkdir -p logs
export PATH="$PATH:/usr/local/bin:$HOME/.local/bin"
PY="$(command -v python3)" || { echo "$(date '+%F %T') không tìm thấy python3" >> logs/fetch.log; exit 1; }
exec 9>/tmp/price_fetch.lock; flock -n 9 || exit 0
echo "=== $(date '+%F %T %Z')" >> logs/fetch.log
timeout 600 "$PY" fetcher.py >> logs/fetch.log 2>&1
timeout 120 "$PY" export_static.py >> logs/fetch.log 2>&1
