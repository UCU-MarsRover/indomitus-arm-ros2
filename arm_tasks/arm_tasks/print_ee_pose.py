import math

import rclpy
from rclpy.node import Node

from tf2_ros import Buffer, TransformListener


class PrintEndEffectorPose(Node):
    def __init__(self):
        super().__init__("print_ee_pose")

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.base_frame = "base_link"
        self.ee_frame = "link_5"

    def run(self):
        self.get_logger().info(
            f"Waiting for TF: {self.base_frame} -> {self.ee_frame}"
        )

        deadline = self.get_clock().now().nanoseconds + int(5.0 * 1e9)

        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)

            try:
                transform = self.tf_buffer.lookup_transform(
                    self.base_frame,
                    self.ee_frame,
                    rclpy.time.Time(),
                )
                self.print_transform(transform)
                return True

            except Exception as exc:
                now = self.get_clock().now().nanoseconds
                if now > deadline:
                    self.get_logger().error(f"Failed to get TF: {exc}")
                    return False

    def print_transform(self, transform):
        t = transform.transform.translation
        q = transform.transform.rotation

        roll, pitch, yaw = quaternion_to_rpy(q.x, q.y, q.z, q.w)

        self.get_logger().info("End-effector pose:")
        print()
        print(f"frame: {self.base_frame} -> {self.ee_frame}")
        print(f"position:")
        print(f"  x: {t.x:.6f}")
        print(f"  y: {t.y:.6f}")
        print(f"  z: {t.z:.6f}")
        print(f"orientation quaternion:")
        print(f"  x: {q.x:.6f}")
        print(f"  y: {q.y:.6f}")
        print(f"  z: {q.z:.6f}")
        print(f"  w: {q.w:.6f}")
        print(f"orientation rpy rad:")
        print(f"  roll:  {roll:.6f}")
        print(f"  pitch: {pitch:.6f}")
        print(f"  yaw:   {yaw:.6f}")
        print()


def quaternion_to_rpy(x, y, z, w):
    sinr_cosp = 2.0 * (w * x + y * z)
    cosr_cosp = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(sinr_cosp, cosr_cosp)

    sinp = 2.0 * (w * y - z * x)
    if abs(sinp) >= 1.0:
        pitch = math.copysign(math.pi / 2.0, sinp)
    else:
        pitch = math.asin(sinp)

    siny_cosp = 2.0 * (w * z + x * y)
    cosy_cosp = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(siny_cosp, cosy_cosp)

    return roll, pitch, yaw


def main():
    rclpy.init()

    node = PrintEndEffectorPose()
    ok = node.run()

    node.destroy_node()
    rclpy.shutdown()

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
