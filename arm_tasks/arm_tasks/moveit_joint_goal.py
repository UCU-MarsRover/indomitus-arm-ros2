import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import Constraints, JointConstraint, MotionPlanRequest, PlanningOptions


class MoveItJointGoal(Node):
    def __init__(self):
        super().__init__("moveit_joint_goal")

        self.client = ActionClient(
            self,
            MoveGroup,
            "/move_action",
        )

        self.joint_names = [
            "joint_0",
            "joint_1",
            "joint_2",
            "joint_3",
            "joint_4",
            "joint_5",
        ]

    def send_goal(self, positions):
        if len(positions) != len(self.joint_names):
            raise ValueError(
                f"Expected {len(self.joint_names)} joint positions, got {len(positions)}"
            )

        self.get_logger().info("Waiting for MoveIt /move_action server...")

        if not self.client.wait_for_server(timeout_sec=10.0):
            self.get_logger().error("MoveIt action server /move_action is not available")
            return False

        request = MotionPlanRequest()
        request.group_name = "arm"
        request.num_planning_attempts = 5
        request.allowed_planning_time = 5.0
        request.max_velocity_scaling_factor = 0.3
        request.max_acceleration_scaling_factor = 0.3

        constraints = Constraints()
        constraints.name = "joint_goal"

        for name, position in zip(self.joint_names, positions):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = float(position)
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)

        request.goal_constraints.append(constraints)

        options = PlanningOptions()
        options.plan_only = False
        options.look_around = False
        options.replan = False

        goal = MoveGroup.Goal()
        goal.request = request
        goal.planning_options = options

        self.get_logger().info(f"Sending MoveIt joint goal: {positions}")

        future = self.client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()

        if goal_handle is None:
            self.get_logger().error("No goal handle returned")
            return False

        if not goal_handle.accepted:
            self.get_logger().error("MoveIt goal rejected")
            return False

        self.get_logger().info("MoveIt goal accepted")

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result
        error_code = result.error_code.val

        if error_code == 1:
            self.get_logger().info("MoveIt goal successfully planned and executed")
            return True

        self.get_logger().error(f"MoveIt failed, error_code={error_code}")
        return False


def main():
    rclpy.init()

    node = MoveItJointGoal()

    if len(sys.argv) == 7:
        positions = [float(x) for x in sys.argv[1:]]
    else:
        positions = [0.0, 0.3, -0.2, 0.2, 0.4, 0.0]

    ok = node.send_goal(positions)

    node.destroy_node()
    rclpy.shutdown()

    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
