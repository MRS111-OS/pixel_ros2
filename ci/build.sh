#!/usr/bin/env bash
# Resolve dependencies and build the Stage 1 packages only.
#
# Vendored upstream packages (navigation2, slam_toolbox, laser_filters, and
# submodules) are not discovered or built. Their declared dependencies are
# satisfied from ROS and Ubuntu packages.
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

: "${ROS_DISTRO:=humble}"

# ROS setup.bash may read unset variables, so disable nounset while sourcing.
set +u
# shellcheck disable=SC1090
source "/opt/ros/${ROS_DISTRO}/setup.bash"
set -u

# Package directories to build, read from the single source of truth.
mapfile -t package_dirs < <(
  sed -e 's/#.*//' -e '/^[[:space:]]*$/d' ci/custom_packages.txt
)

if (( ${#package_dirs[@]} == 0 )); then
  echo 'ERROR: ci/custom_packages.txt contains no package directories.' >&2
  exit 1
fi

for package_dir in "${package_dirs[@]}"; do
  if [[ ! -f "$package_dir/package.xml" ]]; then
    echo "ERROR: package manifest not found: $package_dir/package.xml" >&2
    exit 1
  fi
done

echo "=== Building ${#package_dirs[@]} Stage 1 package directories ==="
printf '  %s\n' "${package_dirs[@]}"

echo
echo '=== rosdep update ==='
rosdep update --rosdistro "$ROS_DISTRO"

echo
echo '=== rosdep install ==='
rosdep install \
  --from-paths "${package_dirs[@]}" \
  --ignore-src \
  --rosdistro "$ROS_DISTRO" \
  -y

# --base-paths prevents colcon from discovering vendor and upstream sources.
echo
echo '=== colcon build (Release) ==='
colcon build \
  --base-paths "${package_dirs[@]}" \
  --event-handlers console_direct+ \
  --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
