import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QLabel,
    QDoubleSpinBox,
    QGridLayout,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
)

from geometry_msgs.msg import TwistStamped
from std_msgs.msg import Int8
from std_srvs.srv import Trigger
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


ACTION_NAME = "/arm_trajectory_controller/follow_joint_trajectory"

JOINT_NAMES = [
    "joint_0",
    "joint_1",
    "joint_2",
    "joint_3",
    "joint_4",
    "joint_5",
]

POSES = {
    "Safe Home":  [0.0,   0.8,  0.6, -0.7, 0.5, 0.0],

    "Front High": [0.0,   0.5,  0.3, -0.4, 0.5, 0.0],
    "Front Mid":  [0.0,   0.8,  0.6, -0.7, 0.5, 0.0],
    "Front Low":  [0.0,   1.1,  0.7, -1.0, 0.5, 0.0],
    "Front Near": [0.0,   0.7, -0.2,  0.2, 0.5, 0.0],
    "Front Far":  [0.0,   0.9,  0.9, -0.5, 0.5, 0.0],

    "Left Mid":   [1.57,  0.8,  0.6, -0.7, 0.5, 0.0],
    "Right Mid":  [-1.57, 0.8,  0.6, -0.7, 0.5, 0.0],
    "Back Mid":   [3.14,  0.8,  0.6, -0.7, 0.5, 0.0],
}


class ArmPanelNode(Node):
    def __init__(self):
        super().__init__("arm_panel")

        self.twist_pub = self.create_publisher(
            TwistStamped,
            "/servo_node/delta_twist_cmds",
            10,
        )

        self.status_value = None
        self.create_subscription(
            Int8,
            "/servo_node/status",
            self.status_cb,
            10,
        )

        self.start_servo_client = self.create_client(
            Trigger,
            "/servo_node/start_servo",
        )

        self.trajectory_client = ActionClient(
            self,
            FollowJointTrajectory,
            ACTION_NAME,
        )

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.speed = 0.015
        self.publish_count = 0

    def status_cb(self, msg):
        self.status_value = msg.data

    def start_servo(self):
        if not self.start_servo_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().error("Servo start service is not available")
            return False

        future = self.start_servo_client.call_async(Trigger.Request())
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)

        if future.result() is None:
            self.get_logger().error("Servo start call failed")
            return False

        ok = future.result().success
        self.get_logger().info(f"Start Servo: success={ok}")
        return ok

    def publish_twist_once(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"

        msg.twist.linear.x = self.vx
        msg.twist.linear.y = self.vy
        msg.twist.linear.z = self.vz

        msg.twist.angular.x = 0.0
        msg.twist.angular.y = 0.0
        msg.twist.angular.z = 0.0

        self.twist_pub.publish(msg)
        self.publish_count += 1

    def stop_twist(self):
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        for _ in range(5):
            self.publish_twist_once()
            time.sleep(0.02)

    def move_joints(self, q, duration_sec=3.0):
        if not self.trajectory_client.wait_for_server(timeout_sec=2.0):
            self.get_logger().error(f"Trajectory action server not available: {ACTION_NAME}")
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = JOINT_NAMES

        point = JointTrajectoryPoint()
        point.positions = [float(x) for x in q]
        point.velocities = [0.0 for _ in q]
        point.time_from_start.sec = int(duration_sec)
        point.time_from_start.nanosec = int((duration_sec - int(duration_sec)) * 1e9)

        goal.trajectory.points.append(point)

        future = self.trajectory_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Joint goal rejected")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        self.get_logger().info(f"Joint pose reached: {q}")
        return True


class ArmPanel(QWidget):
    def __init__(self, node):
        super().__init__()
        self.node = node

        self.setWindowTitle("RoboArm Control Panel")
        self.resize(520, 420)

        self.status_label = QLabel("Servo status: unknown")
        self.cmd_label = QLabel("vx=0.000, vy=0.000, vz=0.000, published=0")

        self.speed_box = QDoubleSpinBox()
        self.speed_box.setDecimals(3)
        self.speed_box.setRange(0.001, 0.050)
        self.speed_box.setSingleStep(0.005)
        self.speed_box.setValue(0.015)
        self.speed_box.valueChanged.connect(self.set_speed)

        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        start_btn = QPushButton("Start Servo")
        start_btn.clicked.connect(self.node.start_servo)

        stop_btn = QPushButton("STOP")
        stop_btn.clicked.connect(self.stop_all)

        top_layout.addWidget(start_btn)
        top_layout.addWidget(stop_btn)
        top_layout.addWidget(QLabel("Speed"))
        top_layout.addWidget(self.speed_box)

        main_layout.addLayout(top_layout)

        pose_group = QGroupBox("Joint Poses")
        pose_layout = QGridLayout()

        pose_names = list(POSES.keys())
        for i, name in enumerate(pose_names):
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, n=name: self.move_pose(n))
            pose_layout.addWidget(btn, i // 3, i % 3)

        pose_group.setLayout(pose_layout)
        main_layout.addWidget(pose_group)

        servo_group = QGroupBox("Servo Cartesian Jog")
        servo_layout = QGridLayout()

        buttons = [
            ("X+", 0, 1, +1, 0, 0),
            ("X-", 2, 1, -1, 0, 0),
            ("Y+", 1, 0, 0, +1, 0),
            ("Y-", 1, 2, 0, -1, 0),
            ("Z+", 0, 3, 0, 0, +1),
            ("Z-", 2, 3, 0, 0, -1),
        ]

        for text, row, col, sx, sy, sz in buttons:
            btn = QPushButton(text)
            btn.pressed.connect(lambda sx=sx, sy=sy, sz=sz: self.set_servo_dir(sx, sy, sz))
            btn.released.connect(self.stop_servo_dir)
            servo_layout.addWidget(btn, row, col)

        servo_group.setLayout(servo_layout)
        main_layout.addWidget(servo_group)

        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.cmd_label)

        self.setLayout(main_layout)

        self.ros_timer = QTimer()
        self.ros_timer.timeout.connect(self.spin_ros)
        self.ros_timer.start(20)

        self.publish_timer = QTimer()
        self.publish_timer.timeout.connect(self.publish_servo)
        self.publish_timer.start(20)

    def set_speed(self, value):
        self.node.speed = float(value)

    def move_pose(self, name):
        self.node.stop_twist()
        q = POSES[name]
        self.node.get_logger().info(f"Moving to pose: {name}")
        self.node.move_joints(q, duration_sec=3.0)

    def set_servo_dir(self, sx, sy, sz):
        v = self.node.speed
        self.node.vx = sx * v
        self.node.vy = sy * v
        self.node.vz = sz * v

    def stop_servo_dir(self):
        self.node.stop_twist()

    def stop_all(self):
        self.node.stop_twist()

    def publish_servo(self):
        if self.node.vx != 0.0 or self.node.vy != 0.0 or self.node.vz != 0.0:
            self.node.publish_twist_once()

        self.cmd_label.setText(
            f"vx={self.node.vx:.3f}, "
            f"vy={self.node.vy:.3f}, "
            f"vz={self.node.vz:.3f}, "
            f"published={self.node.publish_count}"
        )

    def spin_ros(self):
        rclpy.spin_once(self.node, timeout_sec=0.0)

        status = self.node.status_value
        if status is None:
            text = "Servo status: unknown"
        elif status == 0:
            text = "Servo status: 0 OK"
        else:
            text = f"Servo status: {status}"

        self.status_label.setText(text)


def main():
    rclpy.init()
    node = ArmPanelNode()

    app = QApplication(sys.argv)
    panel = ArmPanel(node)
    panel.show()

    code = app.exec_()

    node.stop_twist()
    node.destroy_node()
    rclpy.shutdown()

    sys.exit(code)


if __name__ == "__main__":
    main()
