# 🤖 Titan Robot

This repository contains the ROS 2 packages and configurations for the Titan Robot, including robot bringup, SLAM-based mapping, and localization using slam_toolbox and nav2.

---

## Update system packages

```bash
sudo apt update && sudo apt upgrade -y
```

## Install essential tools

```bash
sudo apt install -y curl wget htop net-tools openssh-server rsync tmux python3 python3-pip python3-rosdep gazebo git python3-colcon-common-extensions terminator


```

```bash
sudo apt install ros-humble-rviz2 ros-humble-slam-toolbox ros-humble-turtlebot3-gazebo ros-humble-joint-state-publisher-gui ros-humble-gazebo-ros-pkgs

```

## One time setup
```bash
echo 'export TURTLEBOT3_MODEL=burger' >> ~/.bashrc
echo 'source /usr/share/gazebo/setup.sh' >> ~/.bashrc
echo 'export GAZEBO_MODEL_PATH=~/titan_ws/src/titan_simulation/turtlebot3_gazebo/models:$GAZEBO_MODEL_PATH' >> ~/.bashrc
echo 'source ~/titan_ws/install/setup.bash' >> ~/.bashrc

```

## To check domain ID: (should show 7)
```bash
echo $ROS_DOMAIN_ID
```

To change domain ID of the terminal
```bash
export ROS_DOMAIN_ID=7
```

---

## 🛠️ Workspace Setup

### ROS 2 Humble on Raspberry Pi 4

To install ROS 2 Humble with a single command on a Raspberry Pi 4 (about 30 minutes, unattended):

```bash
wget -O $HOME/ros2_humble_install.sh https://raw.githubusercontent.com/auromix/ros-install-one-click/main/ros2_humble_install.sh && sudo chmod +x $HOME/ros2_humble_install.sh && bash $HOME/ros2_humble_install.sh && rm $HOME/ros2_humble_install.sh
```

After installation:

```bash
source /opt/ros/humble/setup.bash
printenv | grep ROS
```

Then clone this repository and continue with the workspace steps below.

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

1. **Launch SLAM Toolbox:**
    ```bash
    ros2 launch slam_toolbox online_async_launch.py
    ```

2. **In another terminal, control the robot with teleop:**
    ```bash
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
    ```

3. **Save the map using RViz2:**
    - In Rviz2, go to Panels > Add New Panel > Choose SlamToolboxPlugin
    - Enter your map name beside save map and serialize map
    - Click Save Map and Serialize Map

Note: In rviz, choose Map display and select /map topic
---

## 📍 Localization and Navigation with Saved Map

1. **Stop the SLAM Toolbox launch file.**

2. **Run nav2_bringup:**
    ```bash
    ros2 launch nav2_bringup bringup_launch.py map:=/path/to/your/map.yaml
    ```

3. **In Rviz2:**
    - Click on 2D Pose Estimate and in the map choose approx location of the robot
    - Click the 2D Goal Pose tool
    - Click a point on the map to send the robot to that goal

Note: You can view the following in Rviz:
1. Map->/local_costmap
2. Map->/global_costmap
3. Path->/plan


To send multiple waypoints: 
```bash
ros2 action send_goal /follow_waypoints nav2_msgs/action/FollowWaypoints "poses:
  - header:
      frame_id: map
      stamp: {sec: 0, nanosec: 0}
    pose:
      position: {x: 1.0, y: 1.0}
      orientation: {w: 1.0}
  - header:
      frame_id: map
      stamp: {sec: 0, nanosec: 0}
    pose:
      position: {x: 2.0, y: 1.0}
      orientation: {w: 1.0}
"
```
---

## 📷 Camera Launching

To launch only depth
```bash
ros2 launch realsense2_camera rs_launch.py enable_color:=false enable_infra1:=false enable_infra2:=false enable_depth:=true depth_module.depth_profile:=320x240x6

```

To launch with Infra
```bash
ros2 launch realsense2_camera rs_launch.py enable_color:=false enable_infra1:=true enable_infra2:=true enable_depth:=true depth_module.depth_profile:=320x240x6 infra1_profile:=320x240x6 infra2_profile:=320x240x6

```

To view feed:
1. Go to rviz
2. In display, add Image
3. Choose topic ```/camera/camera/infra2/image_rect_raw``` or ```/camera/camera/infra1/image_rect_raw``` or ```/camera/camera/depth/image_rect_raw```

Troubleshoot:
1. The node begins when you see 
```bash
RealSense Node Is Up!
```

2. If you see 
```bash
The requested device with  is NOT found. Will Try again.
```

OR

```bash
No RealSense devices were found!
```

In this case:
1) Either replug the camera
2) Check ```lsusb```. You should see Intel Corp. Intel(R) RealSense(TM) Depth Camera 435i
If camera is present in lsusb, ```rs-enumerate-devices```
3) Worst case scenario, replug camera from RPI.

---

## 🤖 Robot Simulation

```bash
   ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py 
```

In another terminal:
```bash
    ros2 run teleop_twist_keyboard teleop_twist_keyboard
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

    Note: You can see your ip using ```ip addr```

    You should pick the IP address corresponding to  
    MAC ADDRESS: `88:A2:9E:1B:98:1C`

    This will list all active devices in the range. Look for your robot's IP in the output.

> **Tip:** You may need `sudo` for full results.

## Connecting to Wifi/Hotspot
Ensure you have a device with
Username: ```bvp-titan```
Password: ```titan```

If robot does not connect:
```bash
cd /home/titan/titan_ws/src/shell_scripts
./configure_wifi.sh
```

And restart the robot using
```bash
sudo reboot
```