import math
import time

import rclpy
from tf2_ros import Buffer, TransformListener

from arm_tasks.move_joints import MoveJoints


POSES = [
    ("front_mid",      [0.0,   0.8,  0.6, -0.7, 0.5, 0.0]),
    ("front_high",     [0.0,   0.5,  0.3, -0.4, 0.5, 0.0]),
    ("front_low",      [0.0,   1.1,  0.7, -1.0, 0.5, 0.0]),
    ("front_near",     [0.0,   0.7, -0.2,  0.2, 0.5, 0.0]),
    ("front_far",      [0.0,   0.9,  0.9, -0.5, 0.5, 0.0]),

    ("left_mid",       [1.57,  0.8,  0.6, -0.7, 0.5, 0.0]),
    ("right_mid",      [-1.57, 0.8,  0.6, -0.7, 0.5, 0.0]),
    ("back_mid",       [3.14,  0.8,  0.6, -0.7, 0.5, 0.0]),

    ("left_low",       [1.57,  1.1,  0.7, -1.0, 0.5, 0.0]),
    ("right_low",      [-1.57, 1.1,  0.7, -1.0, 0.5, 0.0]),

    ("home_end",       [0.0,   0.8,  0.6, -0.7, 0.5, 0.0]),
]


def get_pose(node, tf_buffer):
    deadline = time.time() + 2.0

    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        try:
            tf = tf_buffer.lookup_transform("base_link", "link_5", rclpy.time.Time())
            p = tf.transform.translation
            q = tf.transform.rotation
            return p, q
        except Exception:
            pass

    return None, None


def main():
    rclpy.init()

    node = MoveJoints()
    tf_buffer = Buffer()
    tf_listener = TransformListener(tf_buffer, node)

    print("")
    print("=== WORKSPACE PROBE: base_link -> link_5 ===")
    print("name                  j0     j1     j2     j3     j4     j5        x        y        z")
    print("-" * 96)

    for name, q in POSES:
        ok = node.send_goal(q, duration_sec=2.5)

        if not ok:
            print(f"{name:18s} FAILED_GOAL")
            continue

        time.sleep(0.3)
        p, _ = get_pose(node, tf_buffer)

        if p is None:
            print(f"{name:18s} TF_FAILED")
            continue

        print(
            f"{name:18s} "
            f"{q[0]: .2f} {q[1]: .2f} {q[2]: .2f} {q[3]: .2f} {q[4]: .2f} {q[5]: .2f} "
            f"   {p.x: .3f}  {p.y: .3f}  {p.z: .3f}"
        )

    print("-" * 96)
    print("DONE")
    print("")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
