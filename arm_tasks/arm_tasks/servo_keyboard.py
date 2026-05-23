import sys
import threading

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped


class ServoKeyboard(Node):
    def __init__(self):
        super().__init__("servo_keyboard")

        self.publisher = self.create_publisher(
            TwistStamped,
            "/servo_node/delta_twist_cmds",
            10,
        )

        self.frame_id = "base_link"
        self.linear_speed = 0.05

        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0

        self.running = True

        self.timer = self.create_timer(0.05, self.publish_twist)

    def publish_twist(self):
        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.frame_id

        msg.twist.linear.x = self.vx
        msg.twist.linear.y = self.vy
        msg.twist.linear.z = self.vz

        msg.twist.angular.x = 0.0
        msg.twist.angular.y = 0.0
        msg.twist.angular.z = 0.0

        self.publisher.publish(msg)

    def input_loop(self):
        print()
        print("Servo realtime keyboard control for link_5")
        print("Commands + Enter:")
        print("  w : X+")
        print("  s : X-")
        print("  a : Y+")
        print("  d : Y-")
        print("  q : Z+")
        print("  e : Z-")
        print("  z : stop")
        print("  x : exit")
        print()

        while self.running:
            cmd = input("servo> ").strip().lower()

            self.vx = 0.0
            self.vy = 0.0
            self.vz = 0.0

            if cmd == "x":
                self.running = False
                rclpy.shutdown()
                return

            if cmd == "z":
                print("stop")
                continue

            if cmd == "w":
                self.vx = self.linear_speed
            elif cmd == "s":
                self.vx = -self.linear_speed
            elif cmd == "a":
                self.vy = self.linear_speed
            elif cmd == "d":
                self.vy = -self.linear_speed
            elif cmd == "q":
                self.vz = self.linear_speed
            elif cmd == "e":
                self.vz = -self.linear_speed
            else:
                print("unknown command")
                continue

            print(f"vx={self.vx:.3f}, vy={self.vy:.3f}, vz={self.vz:.3f}")


def main():
    rclpy.init()

    node = ServoKeyboard()

    thread = threading.Thread(target=node.input_loop, daemon=True)
    thread.start()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.running = False
    node.destroy_node()

    if rclpy.ok():
        rclpy.shutdown()


if __name__ == "__main__":
    main()
