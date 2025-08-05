#!/bin/bash
set -e

LOG_FILE="$HOME/reverse_tunnel_debug.log"
CONFIG_FILE="$HOME/.ssh/reverse_ssh.conf"
KEY_FILE="$HOME/.ssh/proxyjumper_key"

# Clear or rotate log on start
if [ -f "$LOG_FILE" ] && [ "$(stat -c%s "$LOG_FILE")" -ge 1048576 ]; then
    mv "$LOG_FILE" "$LOG_FILE.old"
fi

# Start fresh log header
echo "========== [$(date)] 🚀 REVERSE TUNNEL SERVICE STARTED ==========" > "$LOG_FILE"

# Load config
source "$CONFIG_FILE"

# Start SSH in background and get its PID
(
  /usr/bin/ssh \
    -o "ServerAliveInterval=60" \
    -o "ServerAliveCountMax=3" \
    -o "StrictHostKeyChecking=accept-new" \
    -i "$KEY_FILE" \
    -N -R /${IDENTIFIER}:localhost:22 ${PROXY_USER}@${PROXY_HOST}
) >> "$LOG_FILE" 2>&1 &

SSH_PID=$!

# Loop with keepalive message
while kill -0 "$SSH_PID" 2>/dev/null; do
  echo "[$(date)] 🔁 KEEPALIVE - SSH tunnel still running" >> "$LOG_FILE"
  sleep 300
done

# Log when tunnel dies
echo "========== [$(date)] ❌ REVERSE TUNNEL SERVICE STOPPED ==========" >> "$LOG_FILE"
exit 1
