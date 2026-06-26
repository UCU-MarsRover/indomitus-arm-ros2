from setuptools import find_packages, setup

package_name = 'arm_tasks'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='UCUSpaceRobotics',
    maintainer_email='indomitus@ucu.edu.ua',
    description='Core control tasks and MoveIt scripts for the Indomitus arm',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'move_joints = arm_tasks.move_joints:main',
            'move_to_point = arm_tasks.move_to_point:main',
            'teleop_servo = arm_tasks.teleop_servo:main',
        ],
    },
)