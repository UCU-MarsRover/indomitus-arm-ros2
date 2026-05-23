import os
import yaml

from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def load_yaml(package_name, relative_path):
    package_path = get_package_share_directory(package_name)
    absolute_path = os.path.join(package_path, relative_path)

    with open(absolute_path, "r") as file:
        return yaml.safe_load(file)


def load_text(package_name, relative_path):
    package_path = get_package_share_directory(package_name)
    absolute_path = os.path.join(package_path, relative_path)

    with open(absolute_path, "r") as file:
        return file.read()


def generate_launch_description():
    robot_description_content = Command([
        "xacro ",
        PathJoinSubstitution([
            FindPackageShare("arm_description"),
            "urdf",
            "arm.urdf.xacro",
        ])
    ])

    robot_description = {
        "robot_description": ParameterValue(
            robot_description_content,
            value_type=str,
        )
    }

    robot_description_semantic = {
        "robot_description_semantic": load_text(
            "arm_moveit_config",
            "config/arm.srdf",
        )
    }

    kinematics = load_yaml(
        "arm_moveit_config",
        "config/kinematics.yaml",
    )

    joint_limits = load_yaml(
        "arm_moveit_config",
        "config/joint_limits.yaml",
    )

    ompl_planning = load_yaml(
        "arm_moveit_config",
        "config/ompl_planning.yaml",
    )

    moveit_controllers = load_yaml(
        "arm_moveit_config",
        "config/moveit_controllers.yaml",
    )

    move_group = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics,
            joint_limits,
            ompl_planning,
            moveit_controllers,
            {
                "moveit_controller_manager": "moveit_simple_controller_manager/MoveItSimpleControllerManager",
                "trajectory_execution.allowed_execution_duration_scaling": 1.2,
                "trajectory_execution.allowed_goal_duration_margin": 0.5,
                "planning_scene_monitor.publish_planning_scene": True,
                "planning_scene_monitor.publish_geometry_updates": True,
                "planning_scene_monitor.publish_state_updates": True,
                "planning_scene_monitor.publish_transforms_updates": True,
            },
        ],
    )

    return LaunchDescription([
        move_group,
    ])
