import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from trajectory_msgs.msg import JointTrajectory
from sensor_msgs.msg import JointState
from std_msgs.msg import Int8


class ServoProbe(Node):
    def __init__(self):
        super().__init__("servo_probe")

        self.cmd_pub = self.create_publisher(
            TwistStamped,
            "/servo_node/delta_twist_cmds",
            10,
        )

        self.traj_count = 0
        self.status_last = None
        self.joint_before = None
        self.joint_after = None

        self.create_subscription(
            JointTrajectory,
            "/arm_trajectory_controller/joint_trajectory",
            self.traj_cb,
            10,
        )

        self.create_subscription(
            Int8,
            "/servo_node/status",
            self.status_cb,
            10,
        )

        self.create_subscription(
            JointState,
            "/joint_states",
            self.joint_cb,
            10,
        )

    def traj_cb(self, msg):
        self.traj_count += 1

    def status_cb(self, msg):
        self.status_last = msg.data

    def joint_cb(self, msg):
        if self.joint_before is None:
            self.joint_before = list(msg.position)
        self.joint_after = list(msg.position)

    def publish_twist(self, vx=0.02, vy=0.0, vz=0.0, duration=3.0, rate_hz=50.0):
        period = 1.0 / rate_hz
        start = time.time()

        while time.time() - start < duration:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "base_link"

            msg.twist.linear.x = vx
            msg.twist.linear.y = vy
            msg.twist.linear.z = vz

            msg.twist.angular.x = 0.0
            msg.twist.angular.y = 0.0
            msg.twist.angular.z = 0.0

            self.cmd_pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.0)
            time.sleep(period)


def main():
    rclpy.init()
    node = ServoProbe()

    node.get_logger().info("Waiting for subscriptions...")
    end = time.time() + 1.0
    while time.time() < end:
        rclpy.spin_once(node, timeout_sec=0.05)

    node.get_logger().info("Publishing +X TwistStamped with real timestamps...")
    node.publish_twist(vx=0.02, vy=0.0, vz=0.0, duration=3.0, rate_hz=50.0)

    end = time.time() + 0.5
    while time.time() < end:
        rclpy.spin_once(node, timeout_sec=0.05)

    print("")
    print("=== SERVO PROBE RESULT ===")
    print(f"trajectory messages: {node.traj_count}")
    print(f"last servo status:   {node.status_last}")
    print(f"joint before:        {node.joint_before}")
    print(f"joint after:         {node.joint_after}")

    if node.joint_before is not None and node.joint_after is not None:
        diffs = [a - b for a, b in zip(node.joint_after, node.joint_before)]
        print(f"joint delta:         {diffs}")

    print("==========================")
    print("")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
