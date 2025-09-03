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
    ros-humble-rviz2 \
    python3 \
    python3-pip \
    python3-rosdep \
    gazebo \  

```

```bash
sudo apt install ros-humble-rviz2 \
    ros-humble-slam-toolbox \
    ros-humble-turtlebot3-gazebo \
    ros-humble-joint-state-publisher-gui \
    ros-humble-gazebo-ros-pkgs

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
    git clone https://github.com/MRS111-OS/titan_robot.git
    mv titan_robot/ src
    ```
3. **Install Dependencies:**
    ```bash
    sudo rosdep init
    rosdep update
    rosdep install --from-paths src --ignore-src -y
    ```

4. **Build the workspace:**
    ```bash
    cd ~/titan_ws
    colcon build --symlink-install --parallel-workers 4
    ```

4. **Source the workspace:**
    ```bash
    source install/setup.bash
    ```

---

## 🚀 Robot Bringup

To start the robot with all required nodes:
```bash
echo 'export TURTLEBOT3_MODEL=burger' >> ~/.bashrc
echo 'source /usr/share/gazebo/setup.sh' >> ~/.bashrc
echo 'export GAZEBO_MODEL_PATH=~/titan_ws/src/titan_simulation/turtlebot3_gazebo/models:$GAZEBO_MODEL_PATH' >> ~/.bashrc
echo 'source ~/titan_ws/install/setup.bash' >> ~/.bashrc

```
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

1. **Stop the SLAM Toolbox launch file. Keep the navigation     launch file running**

2. **Run localization using nav2_bringup:**
    ```bash
    ros2 launch nav2_bringup localization_launch.py map:=/path/to/your/map.yaml
    ```

3. **In Rviz2:**
    - Click on 2D Pose Estimate and in the map choose approx location of the robot
    - Click the 2D Goal Pose tool
    - Click a point on the map to send the robot to that goal

---

## 🤖 Robot Simulation

```bash
   ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py 
```


---

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
