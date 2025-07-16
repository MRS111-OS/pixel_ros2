#!/bin/bash
# Robot Bringup Script
# Version: 1.8
# Date: 2025-06-11
# Author: PS
# Notes: Adds new monitor window, auto recording bms topics to a bag, runs the rosbridge for foxglove

# Function to start roscore in its own window
start_roscore() {
  tmux send-keys -t AMR:roscore "roscore" C-m
  echo "Waiting for roscore to initialize..."
  sleep 2
}

# Function to start the bringup launch file (top-left)
start_amr_bringup() {
  tmux send-keys -t AMR:launch_window.0 "roslaunch titan_bringup amr_bringup.launch" C-m
  echo "Waiting for amr_bringup to initialize..."
  sleep 5
}

# Function to start the MQTT agent launch file (top-right)
start_mqtt_agent() {
  tmux send-keys -t AMR:launch_window.1 "roslaunch titan_bringup realsense_bringup.launch" C-m
  echo "Waiting for mqtt_agent to initialize..."
  sleep 5
}

# Function to start the navigation launch file (middle-left)
start_default_navigation() {
  tmux send-keys -t AMR:launch_window.2 "roslaunch titan_bringup default_navigation.launch" C-m
  echo "Waiting for default_navigation to initialize..."
  sleep 5
}

# Function to start the STM firmware communication node (middle-right)
start_firmware_node() {
  tmux send-keys -t AMR:launch_window.3 "roslaunch mqtt_agent mqtt_agent.launch" C-m
  echo "Waiting for firmware_node to initialize..."
  sleep 5
}

# Function to start the RealSense bringup launch file (bottom-left)
start_realsense_bringup() {
  tmux send-keys -t AMR:launch_window.4 "roslaunch firmware_communication stm_node.launch" C-m
  echo "Waiting for realsense_bringup to initialize..."
  sleep 5
}

# Function to start the DALY-BMS Node launch file (bottom-right)
start_bms_bringup() {
  tmux send-keys -t AMR:launch_window.5 "roslaunch daly_bms_ros daly_bms.launch" C-m
  echo "Waiting for bms to initialize..."
  sleep 5
}

# Function to rosbridge for foxglove
start_foxglove_bridge() {
  # Top pane: monitor topics
  tmux send-keys -t AMR:monitor.0 "roslaunch rosbridge_server rosbridge_websocket.launch address:=192.168.127.224" C-m
}

# Function to record bms topic bags
start_bag_record(){
  # Bottom pane: record bag
  timestamp=$(date +"%Y%m%d_%H%M%S")
  bag_dir="bags/bms_monitor_$timestamp"
  # TODO: Doesn't work, folder creation check
  # Creating directory to save the bags into one folder per session
  mkdir -p "$bag_dir"
  tmux send-keys -t AMR:monitor.1 "until rostopic list | grep -q '/bms/battery_state'; do sleep 1; done; rosbag record --split --duration=60 -O $bag_dir/bms_monitor_$timestamp.bag /bms/alerts /bms/battery_state /bms/temperature" C-m
}

# Main script
ROS_DISTRO="humble"  # ROS distro used

echo "Starting robot bringup..."

# Setup tmux terminal

# Create tmux session and name first window as launch_window
tmux new-session -d -s AMR -n launch_window

# Step 1: Split horizontally → left (pane 0) and right (pane 1)
tmux split-window -h -t AMR:launch_window.0

# Step 2: Split left vertically to make three rows (pane 0, 2, 4)
tmux split-window -v -t AMR:launch_window.0  # Split top-left → middle-left (pane 2)
tmux split-window -v -t AMR:launch_window.2  # Split middle-left → bottom-left (pane 4)

# Step 3: Split right vertically to make three rows (pane 1, 3, 5)
tmux split-window -v -t AMR:launch_window.1  # Split top-right → middle-right (pane 3)
tmux split-window -v -t AMR:launch_window.3  # Split middle-right → bottom-right (pane 5)

# Create new window for roscore
tmux new-window -t AMR -n roscore

# Create new window for monitoring utilities
tmux new-window -t AMR -n monitor

# Split vertically
tmux split-window -v -t AMR:monitor.0

# Start roscore
start_roscore

# Start rosbridge right at the start to get data immediately
start_foxglove_bridge

# Start processes in their assigned panes
start_amr_bringup         # top-left (pane 0)
start_mqtt_agent          # top-right (pane 1)
start_default_navigation  # middle-left (pane 2)
start_firmware_node       # middle-right (pane 3)
start_realsense_bringup   # bottom-left (pane 4)
start_bms_bringup         # bottom-right (pane 5)

# Start bag recording
start_bag_record

# Select main window
tmux select-window -t AMR:launch_window

echo "Robot bringup complete."
echo "Use 'tmux attach -t AMR' to view the session."
