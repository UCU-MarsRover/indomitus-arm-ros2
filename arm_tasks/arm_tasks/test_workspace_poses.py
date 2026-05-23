import time
import rclpy

from arm_tasks.move_joints import MoveJoints

POSES = {
    "safe_front_mid": [0.0, 0.8, 0.6, -0.7, 0.5, 0.0],
    "front_high":     [0.0, 0.6, 0.2, -0.4, 0.5, 0.0],
    "front_low":      [0.0, 1.2, 0.7, -1.0, 0.5, 0.0],
    "front_near":     [0.0, 0.8, -0.4, 0.5, 0.5, 0.0],
    "front_far":      [0.0, 0.9, 0.7, -0.4, 0.5, 0.0],

    "left_mid":       [1.57, 0.8, 0.6, -0.7, 0.5, 0.0],
    "right_mid":      [-1.57, 0.8, 0.6, -0.7, 0.5, 0.0],
    "back_mid":       [3.14, 0.8, 0.6, -0.7, 0.5, 0.0],
}

def main():
    rclpy.init()
    node = MoveJoints()

    for name, q in POSES.items():
        node.get_logger().info(f"Moving to {name}: {q}")
        ok = node.send_goal(q, duration_sec=3)
        if not ok:
            node.get_logger().error(f"Failed pose: {name}")
            break
        time.sleep(1.0)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
