#!/bin/bash
# Robot Bringup Script (ROS 2)
# Version: 2.0
# Date: 2026-01-30
# Author: PS
# Notes:
# - ROS 2 Humble compatible
# - tmux session name: PIXEL
# - Foxglove rosbridge + BMS bag recording

set -e

############################
# Functions
############################

start_pixel_bringup() {
  tmux send-keys -t PIXEL:launch_window.0 \
    "ros2 launch titan_bringup titan_bringup.launch.py" C-m
  sleep 5
}

start_nav2_bringup() {
  tmux send-keys -t PIXEL:launch_window.1 \
    "ros2 launch nav2_bringup bringup_launch.py map:=/home/titan/titan_ws/src/titan_bringup/map/map2.yaml" C-m
  sleep 5
}

start_teleop_keyboard() {
  tmux send-keys -t PIXEL:launch_window.2 \
    "ros2 launch slam_toolbox online_async_launch.py"
  sleep 5
}

start_slam_toolbox() {
  tmux send-keys -t PIXEL:launch_window.3 \
    "ros2 run teleop_twist_keyboard teleop_twist_keyboard" C-m
  sleep 5
}

start_oled() {
  sleep 5
  tmux send-keys -t PIXEL:launch_window.4 \
    "cd /home/titan/titan_ws/src/oled_pkg && python3 oled_ip_pi4.py" C-m
}

############################
# Main
############################

echo "Starting ROS 2 PIXEL bringup..."

source /opt/ros/humble/setup.bash
source ~/titan_ws/install/setup.bash

# Kill any existing PIXEL session to ensure fresh start with updated script
tmux kill-session -t PIXEL 2>/dev/null || true
sleep 1

# Create tmux session
tmux new-session -d -s PIXEL -n launch_window

# Layout: 2 columns × 3 rows
tmux split-window -h -t PIXEL:launch_window.0
tmux split-window -v -t PIXEL:launch_window.0
tmux split-window -v -t PIXEL:launch_window.2
tmux split-window -v -t PIXEL:launch_window.1
tmux split-window -v -t PIXEL:launch_window.3

# Monitor window
tmux new-window -t PIXEL -n monitor
tmux split-window -v -t PIXEL:monitor.0

start_oled
start_pixel_bringup
start_teleop_keyboard
start_nav2_bringup
start_slam_toolbox



tmux select-window -t PIXEL:launch_window

echo "ROS 2 PIXEL bringup complete."
echo "Attach using: tmux attach -t PIXEL"
