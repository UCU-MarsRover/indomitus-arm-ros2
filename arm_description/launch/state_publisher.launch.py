from launch import LaunchDescription
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    urdf_xacro_path = PathJoinSubstitution([
        FindPackageShare("arm_description"),
        "urdf",
        "arm.urdf.xacro",
    ])

    robot_description = {
        "robot_description": Command([
            "xacro ",
            urdf_xacro_path,
        ])
    }

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            robot_description,
            {"use_sim_time": False},
        ],
    )

    joint_state_publisher = Node(
        package="joint_state_publisher",
        executable="joint_state_publisher",
        name="joint_state_publisher",
        output="screen",
        parameters=[
            robot_description,
            {
                "use_sim_time": False,
                "rate": 30,
            },
        ],
    )

    return LaunchDescription([
        robot_state_publisher,
        joint_state_publisher,
    ])
