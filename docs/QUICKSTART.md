# Arm Quickstart

## Table of Contents

**Arm Usage**
* [Starting the Arm on the Jetson](#starting-the-arm-on-the-jetson)
* [Starting the Arm in Simulation (Laptop)](#starting-the-arm-in-simulation-laptop)
* [Turning Off the Arm](#turning-off-the-arm)

**Docker**
* [Getting the Docker Image and Starting the Container](#getting-the-docker-image-and-starting-the-container)
* [Start the Container and Build the Workspace](#start-the-container-and-build-the-workspace)
* [Image Tags Architecture](#image-tags-architecture)

**Scripts**
* [Deployment Script](#deployment-script)
* [Script to Enter Containers](#script-to-enter-containers)

**Project Structure**
* [ROS 2 Packages Overview](#ros2-packages-overview)

**Important ROS 2 and Colcon Commands**
* [Workspace Management (`colcon`)](#workspace-management-colcon)
* [Execution](#execution)
* [Network Introspection & Debugging](#network-introspection--debugging)

---

## Arm Usage

### Starting the Arm on the Jetson

Follow these steps to power on and operate the robotic arm:

1. **Power on the system:** Turn on the main power switch for the rover/arm payload.
2. **Launch the core nodes:** Connect to the Jetson and start the hardware interface to enable CAN communication with the joint actuators.
3. **Control the arm:** Launch the MoveIt Servo node or the custom Python control panel to send trajectory commands to the manipulator.

### Starting the Arm in Simulation (Laptop)

Follow these steps to test the arm mathematically in RViz without physical motors:

1. **Build and start the container:** Please refer to the [Docker setup section](#docker) to complete this step.
2. **Run the standalone launch file:** From the bash terminal inside your Docker container, start the visualization and fake hardware controllers:
```bash
ros2 launch arm_bringup arm_standalone.launch.py
```

### Turning Off the Arm

To power down the arm safely, trigger the Emergency Stop (E-Stop) on the rover to immediately cut power to the actuators, or use the main power switch to turn off the Jetson and CAN bus network.

---

## Docker

### Getting the Docker Image and Starting the Container

Before doing anything, you need to prepare your local environment:

1. Navigate to the root of the `indomitus-arm-ros2` repository.
2. Copy the example Docker Compose file:
```bash
cp ./docker/docker-compose.dev.example.yaml ./docker-compose.yaml
```

Next, you need the Docker image. Build it locally.

```bash
docker compose build
```

> **Note:** All containers mount your local `src/` directory. Ensure you are on the correct branch locally and have pulled the latest changes before starting the container.

### Start the Container and Build the Workspace

1. Start the container in the background:
```bash
docker compose up -d
```
2. Enter the running container:
```bash
docker exec -it arm_dev /bin/bash
```
3. Build the ROS 2 workspace:
```bash
cd /opt/ws
colcon build --symlink-install
source install/setup.bash
```

### Image Tags Architecture

| Tag | Architecture | Use Case |
|---|---|---|
| `local-prod` | — | Production image built locally. |
| `develop-dev` / `main-dev` | AMD64 | Development image built continuously by GitHub workflows. Can be used on standard Intel/AMD laptops for development, simulation, RViz, and MoveIt tuning. |
| `develop-prod` / `main-prod` | ARM64 | Production image built continuously by GitHub workflows. Designed strictly for deployment on the NVIDIA Jetson. Cannot run natively on standard Intel/AMD laptops. |

---

## Scripts

The repository contains utility scripts to simplify common workflow tasks. All scripts are located in the `scripts/` directory.

### TODO Deployment Script

Use the dedicated deployment script to transfer your codebase and Docker environment to the Jetson.

```bash
./scripts/deploy_to_jetson.sh
```

For further details on available deploy modes, refer to `deployment.md`.

### Script to Enter Containers

This script automates the process of opening a bash terminal inside your Docker containers.

Enter the local development container:
```bash
./scripts/enter_container.sh local
```

TODO Enter the remote Jetson container:
```bash
./scripts/enter_container.sh jetson
```

---

## Project Structure

### ROS 2 Packages Overview

* **`arm_description`** — URDF/Xacro models, `.stl` meshes for visuals and collisions, and virtual TCP definitions.
* **`arm_hardware_interface`** — Custom `ros2_control` C++ plugin for parsing CAN bus frames and controlling physical actuators.
* **`arm_moveit_config`** — Configuration files for MoveIt 2 (SRDF, kinematics, limits) and MoveIt Servo.
* **`arm_tasks`** — Python scripts for high-level operations (joint control, Cartesian stepping, GUI control panel).
* **`arm_bringup`** — Launch files to start the entire manipulator subsystem or standalone Fake Hardware components.
* **`arm_sim`** — Packages linking the URDF to the Gazebo physics simulator via `gz_ros2_control`.

---

## Important ROS 2 and Colcon Commands

When developing and debugging the arm, these are the most common commands you will use inside the Docker container.

### Workspace Management (`colcon`)

| Command | Description |
|---|---|
| `colcon build --symlink-install` | Builds the workspace. The symlink flag ensures changes to Python scripts take effect immediately. |
| `colcon build --packages-select <package>` | Builds only the specifically named package, saving time. |
| `rm -rf build/ install/ log/` | Completely cleans the workspace cache. |

### Execution

| Command | Description |
|---|---|
| `ros2 run <package> <executable>` | Starts a single, isolated node (e.g., `ros2 run arm_tasks arm_panel`). |
| `ros2 launch <package> <launch_file.py>` | Starts a complete subsystem (e.g., `ros2 launch arm_bringup arm_standalone.launch.py`). |

### Network Introspection & Debugging

| Command | Description |
|---|---|
| `ros2 control list_controllers` | Displays active trajectory and hardware controllers. |
| `ros2 topic echo /joint_states` | Shows the live angular positions and velocities of the 6 joints. |
| `ros2 topic hz /joint_states` | Calculates the publishing rate of the joint encoders. |
| `ros2 param list` | Lists all configuration parameters available across the currently running nodes. |