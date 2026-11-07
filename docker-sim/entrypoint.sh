#!/usr/bin/env bash
# Headless sim + Nav2 + VDA5050 bridge, equivalent to pixel_simulation's
# bringup_sim.launch.py (gazebo + robot_state_publisher) plus titan_nav's
# nav2.launch.py (map_server + AMCL + the nav stack, titan_nav's own
# warehouse_map.yaml by default) plus mqtt_agent_ros2's
# vda_integrated.launch.py, but:
#  - gazebo runs server-only (-s), since bringup_sim.launch.py hardcodes
#    "-r" with no headless toggle to override via launch arguments.
#  - VDA5050/custom-bridge YAML config (no env-var support in ROS2 Humble's
#    param parser) is generated here from templates, via envsubst, into the
#    *source* tree -- colcon's --symlink-install makes the installed share/
#    copy a symlink back to source for DIRECTORY installs, so writing here
#    is picked up without a rebuild.
# No -u (nounset): ROS2's own setup.bash/local_setup.bash reference
# AMENT_TRACE_SETUP_FILES and friends without defaults -- they're not
# written to be sourced under nounset, and fail immediately if it's on.
set -eo pipefail

: "${MQTT_HOST:?}" "${MQTT_PORT:?}" "${MQTT_USER:?}" "${MQTT_PASSWORD:?}"
: "${ROBOT_MANUFACTURER:?}" "${ROBOT_SERIAL:?}" "${ROBOT_NAME:=$ROBOT_SERIAL}"
# Opt-in: existing deployments never set this (no TLS support existed in
# custom_mqtt_bridge.py's mqtt_client.py before now, and vda5050_connector's
# mqtt_bridge.py infers it from username presence on its own) -- defaulting
# to false here keeps every pre-existing deployment byte-for-byte unchanged.
: "${MQTT_USE_TLS:=false}"
export MQTT_HOST MQTT_PORT MQTT_USER MQTT_PASSWORD ROBOT_MANUFACTURER ROBOT_SERIAL ROBOT_NAME MQTT_USE_TLS

PARAMS_DIR=/opt/pixel_ws/src/pixel_ros2/mqtt_agent_ros2/params
envsubst < /vda5050_config.yaml.tmpl > "$PARAMS_DIR/vda5050_config.yaml"
envsubst < /vda5050_adapter_params.yaml.tmpl > "$PARAMS_DIR/vda5050_adapter_params.yaml"

source /opt/ros/humble/setup.bash
source /opt/pixel_ws/install/setup.bash

# Opt-in software rendering, default off: on a real GPU (this box has an
# NVIDIA A10G via nvidia-container-toolkit), forcing llvmpipe is actively
# wrong -- gpu_lidar's ray-casting silently produces zero /scan data under
# Mesa software rendering (confirmed: camera/depth-camera sensors work fine
# under llvmpipe, gpu_lidar specifically does not, with no error anywhere
# even at gz's -v 4). On a GPU-less host, set FORCE_SOFTWARE_RENDER=1 to get
# the old behavior back (camera-only sensors still work; lidar/AMCL won't).
if [ "${FORCE_SOFTWARE_RENDER:-0}" = "1" ]; then
  export LIBGL_ALWAYS_SOFTWARE=1
fi

SIM_SHARE="$(ros2 pkg prefix pixel_simulation)/share/pixel_simulation"
export GZ_SIM_RESOURCE_PATH="${SIM_SHARE}/worlds:${SIM_SHARE}/models:${GZ_SIM_RESOURCE_PATH:-}"
export IGN_GAZEBO_RESOURCE_PATH="$GZ_SIM_RESOURCE_PATH"
WORLD_FILE="${WORLD_FILE:-${SIM_SHARE}/worlds/small_warehouse.world}"

pids=()
cleanup() { trap - TERM INT; kill "${pids[@]}" 2>/dev/null || true; wait || true; }
trap cleanup TERM INT

echo "[entrypoint] starting gazebo headless: $WORLD_FILE"
ros2 launch ros_gz_sim gz_sim.launch.py gz_args:="${WORLD_FILE} -s -r" &
pids+=("$!")
sleep 5

echo "[entrypoint] spawning robot (robot_state_publisher, gz entity, ros_gz_bridge)"
# Replicates pixel_simulation's robot_state_publisher.launch.py node-for-node,
# minus its unconditional rviz2 node -- rviz needs a display, this container
# has none, and nothing here looks at it; running it would either crash-loop
# or (under Xvfb) burn RAM this box doesn't have to spare for a GUI nobody
# views. robot_description is computed the same way the launch file does it
# (Command([xacro ...]) at launch-parse time), just via a direct xacro call.
TITAN_DESC_SHARE="$(ros2 pkg prefix titan_description)/share/titan_description"
ROBOT_DESCRIPTION="$(xacro "${TITAN_DESC_SHARE}/urdf/titan_sim.urdf" sim_ign:=true)"

ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$ROBOT_DESCRIPTION" &
pids+=("$!")

# NOT added to pids: "create" is a one-shot spawner that exits 0 once the
# entity exists in the sim -- that's success, not a process that should stay
# running. Added to the same wait -n pool as the long-running nodes, its
# normal clean exit was mistaken for a crash, triggering an endless
# restart loop even though nothing was actually broken. Waited on directly
# here instead, so a real spawn failure (nonzero exit) still fails loudly.
ros2 run ros_gz_sim create -topic /robot_description -name pixel_simulation \
  -allow_renaming true -z 0.28 -x 0.0 -y 0.0 -Y 0.0 &
create_pid="$!"
wait "$create_pid"
echo "[entrypoint] entity spawned"

# The lidar sensor now declares an explicit <topic>scan</topic> in
# titan_sim.urdf (matching the camera sensors, which always have had an
# explicit <topic>) -- it published literally nothing at all, under either
# software or real GPU rendering, as long as it relied on Gazebo's default
# auto-generated topic name (.../link/Lidar_Link/sensor/lidar/scan). No
# error anywhere, even at gz's -v 4; every other sensor on this robot that
# works already has an explicit <topic>, this is the one exception that
# didn't, so bridging /scan directly (no remap needed) is the fix.
ros2 run ros_gz_bridge parameter_bridge \
  "/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist" \
  "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock" \
  "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry" \
  "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V" \
  "/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan" \
  "/world/default/model/pixel_simulation/joint_state@sensor_msgs/msg/JointState[ignition.msgs.Model" \
  "/kinect_camera@sensor_msgs/msg/Image[ignition.msgs.Image" \
  "/kinect_camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo" \
  "/kinect_camera/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked" \
  "/camera/color/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image" \
  "/camera/color/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo" \
  --ros-args \
  -r "/world/default/model/pixel_simulation/joint_state:=/joint_states" \
  -r "/kinect_camera/points:=/camera/depth/points" &
pids+=("$!")
sleep 5

# Apostrophe-free on purpose: a plain-English default inside ${VAR:-...}
# with an apostrophe in it broke bash's parser here (unexpected EOF,
# "looking for matching ''" -- the default-value text gets its own
# quote-tokenization pass even nested inside an outer double-quoted
# string), so this is split into its own variable instead of inlined.
MAP_DISPLAY="${MAP_YAML:-titan_nav default: warehouse_map.yaml}"
echo "[entrypoint] starting Nav2 (map_server + AMCL + nav stack), map=$MAP_DISPLAY"
# titan_nav/nav2.launch.py wraps the workspace's own nav2_bringup
# (/opt/pixel_ws/install/nav2_bringup, built from the vendored copy in
# pixel_ros2/navigation2/ -- shadows the apt ros-humble-navigation2 package
# via the normal overlay/underlay precedence) with a default map
# (warehouse_map.yaml) and nav2 params. Confirmed headless by construction,
# not just by flag: this bringup_launch.py declares no use_rviz argument
# and has no rviz action in it at all, unlike upstream nav2_bringup.
ros2 launch titan_nav nav2.launch.py use_sim_time:=true \
  ${MAP_YAML:+"map:=$MAP_YAML"} &
pids+=("$!")
sleep 10

# AMCL has no idea where it is on the map until given an initial pose --
# normally a human clicks "2D Pose Estimate" in RViz. Headless, nobody's
# there to do that, so this publishes it once automatically: (0,0,0),
# matching exactly where the robot was spawned into Gazebo earlier
# (ros_gz_sim create -x 0.0 -y 0.0 -Y 0.0). Assumes warehouse_map.yaml's
# recorded origin is relative to this same world's origin -- true for a
# map actually built by SLAM-driving this world, which is the only way
# this map file could have been produced in the first place.
echo "[entrypoint] publishing initial AMCL pose (0, 0, 0)"
ros2 topic pub --once /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {frame_id: 'map'}, pose: {pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}, covariance: [0.25,0,0,0,0,0, 0,0.25,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0, 0,0,0,0,0,0.0685]}}" \
  || echo "[entrypoint] initial pose publish failed (non-fatal, AMCL just won't localize until one arrives some other way)"

echo "[entrypoint] starting VDA5050 bridge for ${ROBOT_MANUFACTURER}/${ROBOT_SERIAL}"
ros2 launch mqtt_agent_ros2 vda_integrated.launch.py &
pids+=("$!")

# Exit (non-zero, so Docker restarts per the compose policy) the moment any
# of the three dies -- a silently-dead Gazebo/bridge is worse than a restart.
wait -n "${pids[@]}"
exit_code=$?
echo "[entrypoint] a child process exited ($exit_code); shutting down the rest"
cleanup
exit "$exit_code"
