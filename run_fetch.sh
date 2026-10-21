#!/bin/bash
cd /workspace/price-dashboard
exec 9>/tmp/price_fetch.lock; flock -n 9 || exit 0
echo "=== $(date '+%F %T %Z')" >> logs/fetch.log
timeout 600 /usr/bin/python3 fetcher.py >> logs/fetch.log 2>&1
timeout 120 /usr/bin/python3 export_static.py >> logs/fetch.log 2>&1
