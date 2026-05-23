from arm_tasks.move_joints import MoveJoints
import rclpy

SAFE_HOME = [
    0.0,
    0.8,
    0.6,
    -0.7,
    0.5,
    0.0,
]

def main():
    rclpy.init()

    node = MoveJoints()
    ok = node.send_goal(SAFE_HOME, duration_sec=3)

    node.destroy_node()
    rclpy.shutdown()

    if not ok:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
