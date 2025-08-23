# 🤖 Titan Robot

This repository contains the ROS 2 packages and configurations for the Titan Robot, including robot bringup, SLAM-based mapping, and localization using slam_toolbox and nav2.

---

## Update system packages

```bash
sudo apt update && sudo apt upgrade -y
```

## Install essential tools

```bash
sudo apt install -y \
    curl \
    wget \
    htop \
    net-tools \
    openssh-server \
    rsync \
    tmux \
    python3-rosdep \
    ros-humble-turtlebot4-simulator \
    ros-humble-irobot-create-nodes

```

---

## 🛠️ Workspace Setup

1. **Create the ROS 2 workspace and source folder:**
    ```bash
    mkdir -p ~/titan_ws
    cd ~/titan_ws
    ```

2. **Clone the Titan Robot repository:**
    ```bash
    git clone -b v2 https://github.com/MRS111-OS/titan_robot.git
    mv titan_robot/ src
    ```

3. **Install Dependencies:**
    ```bash
    cd ..
    sudo rosdep init
    rosdep update
    rosdep install --from-paths src --ignore-src -y
    ```

4. **Build the workspace:**
    ```bash
    cd ~/titan_ws
    colcon build --symlink-install --parallel-workers 3
    ```

5. **Source the workspace:**
    ```bash
    source install/setup.bash
    ```

---

## 🚀 Robot Bringup

To start the robot with all required nodes:
```bash
ros2 launch titan_bringup titan_bringup.launch.py
```

This will launch:
- Robot URDF
- RViz2
- Joint State Publisher
- LIDAR driver
- ESP32 communication node

---

## 📽️ Mapping Using SLAM

1. **Launch the Nav2 bringup:**
    ```bash
    ros2 launch nav2_bringup navigation_launch.py
    ```

2. **In a new terminal, launch SLAM Toolbox in async mapping mode:**
    ```bash
    ros2 launch slam_toolbox online_async_launch.py
    ```

3. **In another terminal, control the robot with teleop:**
    ```bash
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
    ```

4. **Save the map using RViz2:**
    - In Rviz2, go to Panels > Add New Panel > Choose SlamToolboxPlugin
    - Enter your map name beside save map and serialize map
    - Click Save Map and Serialize Map

---

## 📍 Localization with Saved Map

1. **Stop the SLAM Toolbox launch file.**

2. **Edit the SLAM config for localization:**
    ```bash
    cd ~/titan_ws/src/titan_robot/slam_toolbox/config
    ```

3. **Modify `mapper_params_online_async.yaml`:**
    - Comment out:
        ```yaml
        # mode: mapping
        ```
    - Uncomment and set:
        ```yaml
        mode: localization
        map_file_name: "/absolute/path/to/your/map.yaml"
        map_start_at_dock: true
        ```

4. **Launch SLAM Toolbox in localization mode:**
    ```bash
    ros2 launch slam_toolbox online_async_launch.py
    ```

5. **In RViz2:**
    - Click the 2D Goal Pose tool
    - Click a point on the map to send the robot to that goal

---

## 🚀 Robot Bringup

To start the robot with all required nodes:
```bash
ros2 launch turtlebot4_ignition_bringup turtlebot4_ignition.launch.py 
```

## 🔎 Scan Network Devices

To find the IP addresses of devices (such as your robot) on your local network, use `nmap`:

1. **Install nmap** (if needed):
    ```bash
    sudo apt update
    sudo apt install nmap
    ```

2. **Scan your network** (replace subnet if needed):
    ```bash
    sudo nmap -sn 192.168.127.0/25
    # OR
    sudo nmap -sn 192.168.127.0/24
    ```

    You should pick the IP address corresponding to  
    MAC ADDRESS: `D8:3A:DD:46:FC:C3`

    This will list all active devices in the range. Look for your robot's IP in the output.

> **Tip:** You may need `sudo` for full results.
