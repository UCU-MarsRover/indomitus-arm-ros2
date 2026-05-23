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

    kinematics = load_yaml("arm_moveit_config", "config/kinematics.yaml")

    raw_servo_yaml = load_yaml("arm_moveit_config", "config/servo.yaml")
    servo_params = {
        "moveit_servo": raw_servo_yaml["moveit_servo"]["ros__parameters"]
    }

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node_main",
        name="servo_node",
        output="screen",
        parameters=[
            robot_description,
            robot_description_semantic,
            kinematics,
            servo_params,
        ],
    )

    return LaunchDescription([
        servo_node,
    ])
