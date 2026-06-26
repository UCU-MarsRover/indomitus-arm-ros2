#!/usr/bin/bash

set -e

source_if_exists() {
    local script_path="$1"

    if [ -f "$script_path" ]; then
        # shellcheck disable=SC1090
        source "$script_path"
    fi
}

# -------------------- ROS2 Workspace Setup --------------------

source_if_exists "/opt/ros/${ROS_DISTRO}/setup.bash"
source_if_exists "/opt/ws/install/setup.bash"

echo "[ROS] SUCCESS: Environment ready (${ROS_DISTRO})."

# -------------------- Launch ROS2 nodes --------------------
if [ "${1}" = "autolaunch" ]; then
    echo "[ARM] Starting standalone launch file..."
    ros2 launch arm_bringup arm_integration.launch.py &
    PID1=$!

    export LD_LIBRARY_PATH=/usr/lib/aarch64-linux-gnu/tegra:$LD_LIBRARY_PATH

    wait -n $PID1
    exit $?
fi

exec "$@"