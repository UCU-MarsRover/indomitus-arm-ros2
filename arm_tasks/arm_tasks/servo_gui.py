import sys
import threading

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import TwistStamped
from std_srvs.srv import Trigger

from python_qt_binding.QtCore import QTimer
from python_qt_binding.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QDoubleSpinBox,
    QGroupBox,
)


class ServoGuiNode(Node):
    def __init__(self):
        super().__init__("servo_gui")

        self.publisher = self.create_publisher(
            TwistStamped,
            "/servo_node/delta_twist_cmds",
            10,
        )

        self.start_servo_client = self.create_client(
            Trigger,
            "/servo_node/start_servo",
        )

        self.frame_id = "base_link"

        self.publish_count = 0

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        self.speed = 0.015

        self.timer = self.create_timer(0.02, self.publish_twist)

    def publish_twist(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id

        msg.twist.linear.x = float(self.vx)
        msg.twist.linear.y = float(self.vy)
        msg.twist.linear.z = float(self.vz)

        msg.twist.angular.x = 0.0
        msg.twist.angular.y = 0.0
        msg.twist.angular.z = 0.0

        self.publisher.publish(msg)
        self.publish_count += 1

    def stop(self):
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

    def start_servo(self):
        if not self.start_servo_client.wait_for_service(timeout_sec=2.0):
            self.get_logger().error("Service /servo_node/start_servo is not available")
            return

        request = Trigger.Request()
        future = self.start_servo_client.call_async(request)

        def done_callback(f):
            try:
                response = f.result()
                self.get_logger().info(
                    f"start_servo: success={response.success}, message='{response.message}'"
                )
            except Exception as exc:
                self.get_logger().error(f"start_servo failed: {exc}")

        future.add_done_callback(done_callback)


class ServoGuiWindow(QWidget):
    def __init__(self, node: ServoGuiNode):
        super().__init__()

        self.node = node

        self.setWindowTitle("RoboArm End-Effector Servo Control")
        self.resize(420, 260)

        main = QVBoxLayout()

        title = QLabel("RoboArm end-effector control: link_5")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main.addWidget(title)

        info = QLabel("Hold a button to move. Release to stop.")
        main.addWidget(info)

        speed_row = QHBoxLayout()
        speed_row.addWidget(QLabel("Linear speed, m/s:"))

        self.speed_spin = QDoubleSpinBox()
        self.speed_spin.setDecimals(3)
        self.speed_spin.setSingleStep(0.005)
        self.speed_spin.setMinimum(0.005)
        self.speed_spin.setMaximum(0.05)
        self.speed_spin.setValue(self.node.speed)
        self.speed_spin.valueChanged.connect(self.set_speed)
        speed_row.addWidget(self.speed_spin)

        main.addLayout(speed_row)

        axes_box = QGroupBox("Cartesian axes")
        axes_layout = QVBoxLayout()

        axes_layout.addLayout(self.make_axis_row("X axis", "X-", "X+", self.x_minus, self.x_plus))
        axes_layout.addLayout(self.make_axis_row("Y axis", "Y-", "Y+", self.y_minus, self.y_plus))
        axes_layout.addLayout(self.make_axis_row("Z axis", "Z-", "Z+", self.z_minus, self.z_plus))

        axes_box.setLayout(axes_layout)
        main.addWidget(axes_box)

        buttons = QHBoxLayout()

        start_button = QPushButton("Start Servo")
        start_button.clicked.connect(self.node.start_servo)
        buttons.addWidget(start_button)

        stop_button = QPushButton("STOP ALL")
        stop_button.setStyleSheet("font-weight: bold; background-color: #cc4444; color: white;")
        stop_button.clicked.connect(self.node.stop)
        buttons.addWidget(stop_button)

        main.addLayout(buttons)

        self.status = QLabel("Current command: vx=0.000, vy=0.000, vz=0.000, published=0")
        main.addWidget(self.status)

        self.setLayout(main)

        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_status)
        self.ui_timer.start(100)

    def make_axis_row(self, label, minus_text, plus_text, minus_fn, plus_fn):
        row = QHBoxLayout()

        row.addWidget(QLabel(label))

        minus = QPushButton(minus_text)
        minus.pressed.connect(minus_fn)
        minus.released.connect(self.node.stop)
        row.addWidget(minus)

        stop = QPushButton("STOP")
        stop.clicked.connect(self.node.stop)
        row.addWidget(stop)

        plus = QPushButton(plus_text)
        plus.pressed.connect(plus_fn)
        plus.released.connect(self.node.stop)
        row.addWidget(plus)

        return row

    def set_speed(self, value):
        self.node.speed = float(value)
        self.node.stop()

    def x_plus(self):
        self.node.vx = self.node.speed
        self.node.vy = 0.0
        self.node.vz = 0.0

    def x_minus(self):
        self.node.vx = -self.node.speed
        self.node.vy = 0.0
        self.node.vz = 0.0

    def y_plus(self):
        self.node.vx = 0.0
        self.node.vy = self.node.speed
        self.node.vz = 0.0

    def y_minus(self):
        self.node.vx = 0.0
        self.node.vy = -self.node.speed
        self.node.vz = 0.0

    def z_plus(self):
        self.node.vx = 0.0
        self.node.vy = 0.0
        self.node.vz = self.node.speed

    def z_minus(self):
        self.node.vx = 0.0
        self.node.vy = 0.0
        self.node.vz = -self.node.speed

    def update_status(self):
        self.status.setText(
            f"Current command: "
            f"vx={self.node.vx:.3f}, "
            f"vy={self.node.vy:.3f}, "
            f"vz={self.node.vz:.3f}, "
            f"published={self.node.publish_count}"
        )

    def closeEvent(self, event):
        self.node.stop()
        event.accept()


def main():
    rclpy.init()

    node = ServoGuiNode()

    ros_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    ros_thread.start()

    app = QApplication(sys.argv)
    window = ServoGuiWindow(node)
    window.show()

    exit_code = app.exec_()

    node.stop()
    node.destroy_node()

    if rclpy.ok():
        rclpy.shutdown()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
