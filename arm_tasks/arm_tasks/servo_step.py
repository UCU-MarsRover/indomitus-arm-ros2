import argparse
import time

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped


class ServoStep(Node):
    def __init__(self):
        super().__init__("servo_step")
        self.pub = self.create_publisher(
            TwistStamped,
            "/servo_node/delta_twist_cmds",
            10,
        )

    def run_step(self, vx, vy, vz, duration, rate):
        period = 1.0 / rate
        end_time = time.time() + duration

        while time.time() < end_time:
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "base_link"

            msg.twist.linear.x = float(vx)
            msg.twist.linear.y = float(vy)
            msg.twist.linear.z = float(vz)

            msg.twist.angular.x = 0.0
            msg.twist.angular.y = 0.0
            msg.twist.angular.z = 0.0

            self.pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.0)
            time.sleep(period)

        for _ in range(10):
            msg = TwistStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "base_link"
            self.pub.publish(msg)
            rclpy.spin_once(self, timeout_sec=0.0)
            time.sleep(period)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vx", type=float, default=0.0)
    parser.add_argument("--vy", type=float, default=0.0)
    parser.add_argument("--vz", type=float, default=0.0)
    parser.add_argument("--duration", type=float, default=2.0)
    parser.add_argument("--rate", type=float, default=50.0)
    args = parser.parse_args()

    rclpy.init()
    node = ServoStep()

    time.sleep(0.5)
    node.run_step(args.vx, args.vy, args.vz, args.duration, args.rate)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
