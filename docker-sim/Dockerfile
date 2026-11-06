FROM ros:humble-ros-base

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=humble \
    TURTLEBOT3_MODEL=burger \
    COLCON_WS=/opt/pixel_ws

# Packages pixel_ros2's own README calls for explicitly (gazebo/nav2 extras
# that aren't picked up as rosdep keys), plus build tooling, gz-sim (ROS
# Gazebo meta package, available straight from the ROS Humble apt repo
# already configured in this base image), and gettext-base for envsubst
# (used by the entrypoint to template the VDA5050 YAML configs).
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl wget git tmux python3 python3-pip python3-rosdep \
      python3-colcon-common-extensions build-essential gettext-base \
      ros-humble-rviz2 ros-humble-slam-toolbox ros-humble-turtlebot3-gazebo \
      ros-humble-joint-state-publisher-gui ros-humble-gazebo-ros-pkgs \
      ros-humble-ros-gz ros-humble-navigation2 ros-humble-nav2-bringup \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${COLCON_WS}/src

# "product" is a second, named build context -- this pixel_ros2 checkout
# itself, one level up from this directory (see docker-compose.pixel-sim.
# yml's additional_contexts) -- kept separate from this directory's own
# default context (Dockerfile/entrypoint/templates) specifically so an
# entrypoint-only edit doesn't invalidate this COPY's cache, and with it
# the ~45-70min colcon build layer below -- which happened three times
# before this split.
COPY --from=product . pixel_ros2

# pixel_ros2 carries many hardware-driver packages this sim+bridge doesn't
# need (lidar, real cameras, AprilTag, coverage planning...), some of whose
# rosdep keys aren't even resolvable on this apt mirror (ros-humble-test-msgs,
# ros-humble-hls-lfcd-lds-driver). --packages-up-to scopes both rosdep and
# colcon to just pixel_simulation + mqtt_agent_ros2 and their actual
# dependency closure, sidestepping all of that rather than chasing missing
# packages for things we'll never launch.
# apt-get update: the previous layer's `rm -rf /var/lib/apt/lists/*` wiped
# the index, and rosdep's internal `apt-get install` doesn't refresh it
# itself -- without this, every apt-backed rosdep key fails "Unable to
# locate package" regardless of whether it actually exists.
# -t build -t buildtool -t exec (omitting "test"): skips every test_depend
# in one shot (ament_lint_auto/common and friends, the dedicated lint
# packages, test_msgs) instead of chasing them one at a time via skip-keys.
# -DBUILD_TESTING=OFF: some packages (nav2_util) unconditionally configure
# their test/ subdirectory regardless of what rosdep installed, which still
# needs test_msgs at CMake-configure time -- this is the actual fix for
# that, not a missing rosdep key.
RUN . /opt/ros/${ROS_DISTRO}/setup.sh \
    && apt-get update \
    && cd ${COLCON_WS} \
    && NEEDED_PATHS=$(colcon list --packages-up-to pixel_simulation mqtt_agent_ros2 titan_description --paths-only) \
    && (rosdep init || true) && rosdep update \
    && rosdep install --from-paths $NEEDED_PATHS --ignore-src -y -t build -t buildtool -t exec \
    && rm -rf /var/lib/apt/lists/* \
    && pip3 install --no-cache-dir -r src/pixel_ros2/mqtt_agent_ros2/requirments.txt \
    && colcon build --symlink-install --parallel-workers 2 --packages-up-to pixel_simulation mqtt_agent_ros2 titan_description \
         --cmake-args -DBUILD_TESTING=OFF

# Default context now (this directory itself), not "product" -- these three
# are the only files that change often, and now the only ones whose edits
# cost a cheap rebuild instead of a full recompile.
COPY entrypoint.sh /entrypoint.sh
COPY vda5050_config.yaml.tmpl /vda5050_config.yaml.tmpl
COPY vda5050_adapter_params.yaml.tmpl /vda5050_adapter_params.yaml.tmpl
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
