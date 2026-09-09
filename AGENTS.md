# Titan Robot - Agent Instructions

## Cursor Cloud specific instructions

### Environment overview

This is a **ROS 2 Jazzy** workspace for the Titan Robot (differential-drive mobile robot). The VM runs Ubuntu 24.04; ROS 2 Jazzy (not Humble) is used because Humble targets Ubuntu 22.04 only.

### Key packages (custom, built from source)

| Package | Type | Purpose |
|---------|------|---------|
| `titan_nav` | ament_cmake | Gazebo simulation, navigation launch files, URDF |
| `titan_description` | ament_cmake | Robot URDF model and meshes |
| `titan_bringup` | ament_cmake | Real-robot bringup launch files |
| `ros_esp_bridge` | ament_cmake | Serial bridge between ROS 2 and ESP32 |
| `sllidar_ros2` | ament_cmake | SLiDAR/RPLidar ROS 2 driver (C++) |

The `navigation2/` and `slam_toolbox/` directories are included in the repo but should NOT be built from source — they are installed via apt as `ros-jazzy-navigation2` and `ros-jazzy-slam-toolbox`.

### Build commands

```bash
source /opt/ros/jazzy/setup.bash
cd /workspace
colcon build --packages-select titan_description titan_bringup titan_nav ros_esp_bridge sllidar_ros2 --symlink-install
source install/setup.bash
```

### Lint / Test

```bash
colcon test --packages-select titan_nav ros_esp_bridge sllidar_ros2
colcon test-result --verbose
```

Note: Existing code has pre-existing flake8 and uncrustify failures (style issues in the repo code). These are NOT environment issues.

### Running the application

- **Simulation (requires display/Gazebo):** `ros2 launch titan_nav bringup.launch.py`
- **Robot state publisher (headless):** `ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(xacro /workspace/install/titan_nav/share/titan_nav/urdf/titan.urdf sim_ign:=true)"`
- **Teleop:** `ros2 run teleop_twist_keyboard teleop_twist_keyboard`

### Important caveats

1. **Compiler**: The default system compiler is Clang 18, but ROS 2 C++ packages must be built with GCC (g++). The update-alternatives are set to prefer GCC, but if builds fail with `'csignal' file not found` or `'iostream' file not found`, ensure `cc`/`c++` point to `gcc`/`g++`.

2. **libstdc++ symlink**: A symlink `/usr/lib/x86_64-linux-gnu/libstdc++.so -> libstdc++.so.6` is required for the linker. If builds fail with `cannot find -lstdc++`, recreate it.

3. **Gazebo simulation** requires a display (X11/Wayland). In headless environments, test with `robot_state_publisher` + topic publishing instead.

4. **Source setup files** before any ROS 2 command:
   ```bash
   source /opt/ros/jazzy/setup.bash
   source /workspace/install/setup.bash
   ```
