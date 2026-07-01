# Arm Quickstart

## Table of Contents

**Arm Usage**
* [Starting the Arm on the Jetson](#starting-the-arm-on-the-jetson)
* [Starting the Arm in Simulation (Laptop)](#starting-the-arm-in-simulation-laptop)
  * [Standalone Visualization](#standalone-visualization)
  * [MoveIt Planning Simulation](#moveit-planning-simulation)
  * [Fake Hardware vs. Real Hardware](#fake-hardware-vs-real-hardware)
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

There are two simulation modes available locally. Choose based on what you need:

| Mode | Launch file | Use case |
|---|---|---|
| Standalone visualization | `arm_bringup/arm_standalone.launch.py` | Quick URDF/mesh checks, manual joint testing via GUI, no planning needed |
| MoveIt planning simulation | `arm_moveit_config/demo.launch.py` | Testing trajectories, kinematics, motion planning, task development |

#### Standalone Visualization

Starts RViz with the Joint State Publisher GUI but no motion planning stack. Useful for quickly
inspecting the URDF model, meshes, and TF tree without loading ros2_control or the full MoveIt overhead.

1. **Allow GUI access:** Run the following command on your **host machine** terminal (not inside Docker) before launching:
```bash
   xhost +local:docker
```
2. **Build and start the container:** Please refer to the [Docker setup section](#docker) to complete this step.
3. **Run the standalone launch file:** From the bash terminal inside your Docker container:
```bash
   ros2 launch arm_bringup arm_standalone.launch.py
```

By default this runs with `use_fake_hardware:=true`, which loads `mock_components/GenericSystem`
(see [Fake Hardware vs. Real Hardware](#fake-hardware-vs-real-hardware) below). To attempt loading
the real CAN hardware interface instead:
```bash
   ros2 launch arm_bringup arm_standalone.launch.py use_fake_hardware:=false
```

#### MoveIt Planning Simulation

Starts the full MoveIt 2 stack with motion planning, collision checking, and trajectory
execution using Fake Hardware. This is the primary mode for developing and testing arm
movements locally.

1. **Allow GUI access:** Run the following command on your **host machine** terminal (not inside Docker) before launching:
```bash
   xhost +local:docker
```
2. **Build and start the container:** Please refer to the [Docker setup section](#docker) to complete this step.
3. **Run the MoveIt demo launch file:** From the bash terminal inside your Docker container:
```bash
   ros2 launch arm_moveit_config demo.launch.py
```

In RViz, use the **MotionPlanning** panel to set a goal pose for the end-effector and click
**Plan & Execute** to run a full plan-and-execute cycle.

#### Fake Hardware vs. Real Hardware

The `arm_macro.xacro` model exposes a `use_fake_hardware` xacro argument that controls which
`ros2_control` hardware plugin gets loaded:

| Value | Plugin | Behavior |
|---|---|---|
| `true` (default) | `mock_components/GenericSystem` | Joint commands are written directly into the joint state and read back immediately — no physics, no motor, no delay. Useful for testing planning logic, SRDF groups, and the MoveIt API without any physical or simulated dynamics. |
| `false` | `arm_hardware_interface/ArmCanSystem` | Sends commands over the real CAN bus to the physical actuators. Requires the Jetson and a working `arm_hardware_interface` build. |

Because `mock_components/GenericSystem` reports back whatever position it was just told to move
to, it does **not** validate motor dynamics, CAN latency, encoder noise, or mechanical limits like
backlash or sag — only the kinematic/geometric correctness of a trajectory is verified.

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

> **GUI Requirement:** If you plan to run simulation tools like RViz on your local laptop, you must allow Docker to access your host machine's display server. Run the following command in your **host machine's terminal** (not inside Docker) before proceeding:
> ```bash
> xhost +local:docker
> ```

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

### Container Autolaunch Behavior

The Docker environment is configured with an `entrypoint.bash` script. When deployed on the Jetson, the production container is set to automatically run this script with the `autolaunch` argument. This automatically sources the workspace and launches the core ROS 2 nodes without requiring an SSH connection.

If you need to test the autolaunch sequence locally inside your development container, you can trigger it manually:
```bash
/entrypoint.bash autolaunch
```

Note: Ensure your workspace is built (colcon build) before testing the autolaunch locally, otherwise the script will not find the required packages.

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
* **`arm_moveit_config`** — MoveIt 2 configuration and launch infrastructure. Contains the SRDF, kinematics solver config (`kinematics.yaml`), joint limits, OMPL/Pilz planner settings, and controller mappings (`moveit_controllers.yaml`, `ros2_controllers.yaml`). Provides a full set of launch files: `demo.launch.py` for standalone simulation with motion planning, plus modular files (`move_group.launch.py`, `moveit_rviz.launch.py`, `spawn_controllers.launch.py`, etc.) for flexible bringup on the Jetson.
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
| `ros2 run <package> <executable>` | Starts a single, isolated node. |
| `ros2 launch <package> <launch_file.py>` | Starts a complete subsystem. |
| `ros2 launch arm_bringup arm_standalone.launch.py` | Standalone RViz visualization with GUI sliders, no ros2_control or planning. |
| `ros2 launch arm_moveit_config demo.launch.py` | Full MoveIt simulation with motion planning and RViz. |

### Network Introspection & Debugging

| Command | Description |
|---|---|
| `ros2 control list_controllers` | Displays active trajectory and hardware controllers. |
| `ros2 topic echo /joint_states` | Shows the live angular positions and velocities of the 6 joints. |
| `ros2 topic hz /joint_states` | Calculates the publishing rate of the joint encoders. |
| `ros2 param list` | Lists all configuration parameters available across the currently running nodes. |
| `ros2 action list` | Lists active action servers, including MoveIt's `/move_action`. |
| `ros2 action info /move_action` | Shows goal, result, and feedback types for the MoveIt planning action. |
| `ros2 topic echo /display_planned_path` | Streams the planned trajectory as it is computed by `move_group`. |