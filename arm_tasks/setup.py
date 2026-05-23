from setuptools import setup

package_name = "arm_tasks"

setup(
    name=package_name,
    version="0.0.1",
    packages=[package_name],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="user",
    maintainer_email="user@example.com",
    description="Task-level test scripts for the robotic arm.",
    license="MIT",
    entry_points={
        "console_scripts": [
            'servo_step = arm_tasks.servo_step:main',
            'arm_panel = arm_tasks.arm_panel:main',
            'servo_probe = arm_tasks.servo_probe:main',
            'workspace_probe = arm_tasks.workspace_probe:main',
            "move_joints = arm_tasks.move_joints:main",
            "move_home = arm_tasks.move_home:main",
            "move_safe_home = arm_tasks.move_safe_home:main",
            "moveit_joint_goal = arm_tasks.moveit_joint_goal:main",
            "print_ee_pose = arm_tasks.print_ee_pose:main",
            "teleop_ee_keyboard = arm_tasks.teleop_ee_keyboard:main",
            "servo_keyboard = arm_tasks.servo_keyboard:main",
            "servo_gui = arm_tasks.servo_gui:main",
            'test_workspace_poses = arm_tasks.test_workspace_poses:main',
        ],
    },
)
