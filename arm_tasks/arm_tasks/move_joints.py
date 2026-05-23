import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint


class MoveJoints(Node):
    def __init__(self):
        super().__init__("move_joints")

        self.client = ActionClient(
            self,
            FollowJointTrajectory,
            "/arm_trajectory_controller/follow_joint_trajectory",
        )

        self.joint_names = [
            "joint_0",
            "joint_1",
            "joint_2",
            "joint_3",
            "joint_4",
            "joint_5",
        ]

    def send_goal(self, positions, duration_sec=3):
        if len(positions) != len(self.joint_names):
            raise ValueError(
                f"Expected {len(self.joint_names)} positions, got {len(positions)}"
            )

        self.get_logger().info("Waiting for trajectory action server...")

        if not self.client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("Action server is not available")
            return False

        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = self.joint_names

        point = JointTrajectoryPoint()
        point.positions = [float(x) for x in positions]
        point.velocities = [0.0] * len(self.joint_names)
        point.time_from_start.sec = int(duration_sec)
        point.time_from_start.nanosec = 0

        goal.trajectory.points.append(point)

        self.get_logger().info(f"Sending goal: {positions}")

        future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected")
            return False

        self.get_logger().info("Goal accepted")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result

        if result.error_code == 0:
            self.get_logger().info("Goal successfully reached")
            return True

        self.get_logger().error(
            f"Goal failed: code={result.error_code}, message='{result.error_string}'"
        )
        return False


def main():
    rclpy.init()

    node = MoveJoints()

    if len(sys.argv) == 7:
        positions = [float(x) for x in sys.argv[1:]]
    else:
        positions = [0.0, 0.4, -0.3, 0.2, 0.5, 0.0]

    ok = node.send_goal(positions)

    node.destroy_node()
    rclpy.shutdown()

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
