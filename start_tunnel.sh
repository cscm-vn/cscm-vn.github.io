#!/bin/bash
# Optional: Cloudflare quick tunnel (random URL, changes on every restart). Needs outbound TCP/UDP 7844.
cd /workspace/price-dashboard
pkill -f "cloudflared tunnel --url"; : > logs/tunnel.log
setsid nohup cloudflared tunnel --no-autoupdate --protocol http2 --url http://127.0.0.1:8080 >> logs/tunnel.log 2>&1 < /dev/null &
for i in $(seq 1 40); do grep -q "Registered tunnel connection" logs/tunnel.log && break; sleep 1; done
if grep -q "Registered tunnel connection" logs/tunnel.log; then
  grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' logs/tunnel.log | head -1 | tee data/tunnel_url.txt
else echo "Tunnel FAILED (see logs/tunnel.log)"; pkill -f "cloudflared tunnel --url"; exit 1; fi
