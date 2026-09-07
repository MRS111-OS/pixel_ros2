# titan_description

The `titan_description` package contains the URDF files and meshes required for both the simulation and the physical visualization of the Pixel robot.

---

## 📄 URDF Overview

This package provides two main URDF files, each serving a specific purpose in the ROS 2 ecosystem:

### 1. `titan.urdf`
* **Purpose:** Used by the `robot_state_publisher` when operating the **actual physical robot**.
* **Visualization:** Responsible for publishing the links, joints, and meshes for RViz.
* **Requirement:** Mesh files will only be visualized in RViz if the package is built and the setup script is sourced in the terminal where RViz is launched.

### 2. `titan_sim.urdf`
* **Purpose:** Used strictly for **simulation**, currently optimized for **Ignition Gazebo 6**.
* **Features:** Contains essential physics properties and hardware plugins to simulate the robot's movement and sensor suite.

---

## 🛠 Ignition Gazebo Plugins

The `titan_sim.urdf` utilizes the following plugins to bridge the gap between simulation and ROS 2:

| Plugin Name | Description |
| :--- | :--- |
| **Gz Sensors System** (`gz-sim-sensors-system`) | Manages the sensor rendering pipeline using the `ogre2` engine. |
| **Joint State Publisher** (`gz-sim-joint-state-publisher-system`) | Publishes the states of the robot's joints within the simulation. |
| **Differential Drive** (`gz-sim-diff-drive-system`) | Controls the `Left_Wheel_Joint` and `Right_Wheel_Joint`. Subscribes to `/cmd_vel` and publishes odometry to `/odom`. |
| **Odometry Publisher** (`ignition-gazebo6-odometry-publisher-system`) | Broadcasts the transform (TF) between the `odom` frame and the `base_footprint` frame. |
| **GPU Lidar** | Simulates a laser scanner on the `Lidar_Link` with 720 samples and a 15m range. |
| **Depth Camera** | Simulates a Kinect-style depth sensor on the `Depth_Camera_Link`. |
| **RGB Camera** | Simulates a stereo camera setup (Left and Right) for visual data. |

---

## 🔍 Mesh Path Compatibility

A key technical difference between the two files is how they reference mesh resources to ensure they are found correctly by different tools:

* **In `titan.urdf`:** Meshes are called using the standard package URI:  
  `package://titan_description/<path_to_file>`  
  *This ensures RViz can locate the files via the ROS 2 environment.*

* **In `titan_sim.urdf`:** Meshes are called using the substitution command:  
  `file://$(find titan_description)/<path_to_file>`  
  *This allows Ignition Gazebo to resolve paths dynamically across different system configurations without compatibility issues.*