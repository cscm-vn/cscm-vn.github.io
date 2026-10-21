#!/bin/bash
# Keeps web server + Cloudflare quick tunnel alive. Run every 5 min from cron.
cd /workspace/price-dashboard
export PATH=/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin
if ! curl -sf -m 5 http://127.0.0.1:8080/healthz >/dev/null; then
  pkill -f "gunicorn.*app:app"; sleep 1
  setsid nohup python3 -m gunicorn -w 2 -b 0.0.0.0:8080 app:app >> logs/server.log 2>&1 < /dev/null &
  echo "$(date '+%F %T') restarted server" >> logs/watchdog.log
fi
