from arm_tasks.move_joints import MoveJoints

import rclpy


def main():
    rclpy.init()

    node = MoveJoints()
    ok = node.send_goal([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    node.destroy_node()
    rclpy.shutdown()

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
