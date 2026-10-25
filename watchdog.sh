#!/bin/bash
# Keeps web server + Cloudflare quick tunnel alive. Run every 5 min from cron.
# Chạy được từ bất kỳ clone nào: tự chuyển vào thư mục chứa script (kể cả khi cron gọi bằng đường dẫn tuyệt đối).
cd "$(dirname "$(readlink -f "$0")")" || exit 1
mkdir -p logs
export PATH=/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin
PY="$(command -v python3)" || { echo "$(date '+%F %T') không tìm thấy python3" >> logs/watchdog.log; exit 1; }
if ! curl -sf -m 5 http://127.0.0.1:8080/healthz >/dev/null; then
  pkill -f "gunicorn.*app:app"; sleep 1
  setsid nohup "$PY" -m gunicorn -w 2 -b 0.0.0.0:8080 app:app >> logs/server.log 2>&1 < /dev/null &
  echo "$(date '+%F %T') restarted server" >> logs/watchdog.log
fi
