from launch import LaunchDescription
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    urdf_xacro_path = PathJoinSubstitution([
        FindPackageShare("arm_description"),
        "urdf",
        "arm.urdf.xacro",
    ])

    controllers_path = PathJoinSubstitution([
        FindPackageShare("arm_control"),
        "config",
        "controllers.yaml",
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
        parameters=[robot_description],
    )

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        name="controller_manager",
        output="screen",
        parameters=[
            robot_description,
            controllers_path,
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
        output="screen",
    )

    arm_trajectory_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "arm_trajectory_controller",
            "--controller-manager",
            "/controller_manager",
            "--param-file",
            controllers_path,
        ],
        output="screen",
    )

    delay_arm_controller = RegisterEventHandler(
        OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[arm_trajectory_controller_spawner],
        )
    )

    return LaunchDescription([
        robot_state_publisher,
        ros2_control_node,
        joint_state_broadcaster_spawner,
        delay_arm_controller,
    ])
