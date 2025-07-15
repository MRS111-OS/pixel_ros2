#!/bin/bash

# CONFIG
SESSION_NAME="amr_dashboard"
BASE_DIR="$HOME/AMR_DASHBOARD"
BACKEND_DIR="$BASE_DIR/AMR-backend"
FRONTEND_DIR="$BASE_DIR/AMR-frontend"
FRONTEND_PORT=4200
DATE=$(date +"%Y-%m-%d_%H-%M-%S")
LOG_DIR="$BASE_DIR/logs/$DATE"

mkdir -p "$LOG_DIR"

# Log everything from this point forward
exec > >(tee -a "$LOG_DIR/start_dashboard.log") 2>&1

echo "========== AMR Dashboard Startup =========="
echo "Log directory: $LOG_DIR"

# Create or update symlink to latest log folder
ln -sfn "$LOG_DIR" "$BASE_DIR/logs/latest"
echo "Symlink updated: $BASE_DIR/logs/latest -> $LOG_DIR"

# === Determine local IP for frontend ===
FRONTEND_HOST=$(hostname -I | awk '{print $1}')
echo "Determined frontend host IP: $FRONTEND_HOST"

# === Check MongoDB status ===
echo "Checking MongoDB on port 27017..."

if nc -z localhost 27017; then
    echo "MongoDB is running on port 27017."
else
    echo "MongoDB is NOT running. Attempting to start via systemctl..."
    sudo systemctl start mongod

    sleep 3

    if nc -z localhost 27017; then
        echo "MongoDB started successfully via systemctl."
    else
        echo "systemctl start failed or MongoDB not installed as service. Attempting to start mongod manually..."
        mongod --fork --logpath "$LOG_DIR/mongodb.log"

        sleep 3

        if nc -z localhost 27017; then
            echo "MongoDB started successfully via mongod."
        else
            echo "⚠️  Failed to start MongoDB! Please check logs at $LOG_DIR/mongodb.log"
        fi
    fi
fi

# === Check MQTT (Mosquitto) status ===
echo "Checking MQTT broker (Mosquitto) on port 1883..."

if nc -z localhost 1883; then
    echo "MQTT broker is running on port 1883."
else
    echo "MQTT broker is NOT running. Attempting to start Mosquitto via systemctl..."
    sudo systemctl restart mosquitto

    sleep 3

    if nc -z localhost 1883; then
        echo "Mosquitto started successfully."
    else
        echo "⚠️  Failed to start Mosquitto. Please check systemctl or journal logs."
    fi
fi

# === Kill any existing frontend process ===
echo "Checking for process on frontend port $FRONTEND_PORT..."
PID=$(lsof -ti tcp:$FRONTEND_PORT)
if [ -n "$PID" ]; then
    echo "Killing process on frontend port $FRONTEND_PORT (PID: $PID)..."
    kill -9 $PID
else
    echo "No process running on frontend port $FRONTEND_PORT."
fi

# === Kill existing tmux session ===
echo "Checking existing tmux session..."
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Existing tmux session '$SESSION_NAME' found. Killing..."
    tmux kill-session -t "$SESSION_NAME"
else
    echo "No existing tmux session."
fi

# === Start new tmux session with split panes ===
echo "Starting new tmux session '$SESSION_NAME' with split panes..."
tmux new-session -d -s "$SESSION_NAME" -n "dashboard" \
    "cd $BACKEND_DIR && npm install && npm run start:dev 2>&1 | tee $LOG_DIR/backend.log"

tmux split-window -h -t "$SESSION_NAME:0" \
    "cd $FRONTEND_DIR && npm install && ng serve --host "$FRONTEND_HOST" --port "$FRONTEND_PORT" 2>&1 | tee $LOG_DIR/frontend.log"

tmux select-layout -t "$SESSION_NAME" even-horizontal

echo "✅ Dashboard servers started in tmux session '$SESSION_NAME'. Attaching..."
tmux attach -t "$SESSION_NAME"
