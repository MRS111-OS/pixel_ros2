# Git submodules setup

This repo uses Git submodules for dependencies. Submodules and their branches are defined in [.gitmodules](.gitmodules).

## Quick start

### Clone repo with all submodules

```bash
git clone --recurse-submodules <repo-url>
cd pixel_ros2
```

### Existing clone: fetch and sync all submodules

```bash
git submodule update --init --recursive
git submodule sync
git submodule update --remote --recursive
```

- **`update --init --recursive`** — Clone any missing submodules and check out the commit recorded by this repo.
- **`sync`** — Update submodule URLs and branch config from `.gitmodules`.
- **`update --remote --recursive`** — In each submodule, fetch and check out the **branch** listed in `.gitmodules` and update to the latest commit on that branch.

## Submodule inventory

| Path | Repository | Branch | Description |
|---|---|---|---|
| `momentum_shell_scripts` | [MRS111-OS/momentum_shell_scripts](https://github.com/MRS111-OS/momentum_shell_scripts) | `main` | Shell scripts for robot startup, environment and WiFi config |
| `micro-ROS-Agent` | [micro-ROS/micro-ROS-Agent](https://github.com/micro-ROS/micro-ROS-Agent) | `humble` | micro-ROS agent bridging ESP32 firmware to ROS 2 |
| `mqtt_agent_ros2` | [MRS111-OS/mqtt_agent_ros2](https://github.com/MRS111-OS/mqtt_agent_ros2) | `feature/vda5050-integration` | MQTT bridge for VDA 5050 fleet management |
| `ros_amr_interop` | [inorbit-ai/ros_amr_interop](https://github.com/inorbit-ai/ros_amr_interop) | `humble-devel` | AMR interoperability (InOrbit integration) |
| `robot_firmware_interface` | [MRS111-OS/robot_firmware_interface](https://github.com/MRS111-OS/robot_firmware_interface) | `main` | Custom ROS 2 msgs/srvs for ESP32 firmware peripherals (LCD, battery, buzzer, LEDs, GPIO, IMU) |

## Submodule branches

Branches are set in `.gitmodules`. To use the latest commit on each submodule's branch:

```bash
git submodule sync
git submodule update --remote --recursive
```

To record the new submodule commits in this repo:

```bash
git add .
git commit -m "Update submodules to latest on configured branches"
```

## Check status

```bash
git submodule status
```

## Check out a specific branch in one submodule

```bash
cd <submodule-path>
git fetch origin
git checkout <branch-name>
cd ..
```

## Add a new submodule

```bash
git submodule add -b <branch-name> <repo-url> <path>
git add .gitmodules <path>
git commit -m "Add <name> submodule"
```
