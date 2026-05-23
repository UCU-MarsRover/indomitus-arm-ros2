import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node

from geometry_msgs.msg import PoseStamped
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    Constraints,
    MotionPlanRequest,
    PlanningOptions,
    PositionConstraint,
    BoundingVolume,
    JointConstraint,
)
from shape_msgs.msg import SolidPrimitive
from tf2_ros import Buffer, TransformListener


class EndEffectorKeyboardTeleop(Node):
    def __init__(self):
        super().__init__("teleop_ee_keyboard")

        self.base_frame = "base_link"
        self.ee_frame = "link_5"
        self.group_name = "arm"
        self.step = 0.03

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.moveit_client = ActionClient(self, MoveGroup, "/move_action")

        self.joint_names = [
            "joint_0",
            "joint_1",
            "joint_2",
            "joint_3",
            "joint_4",
            "joint_5",
        ]

    def get_current_pose(self):
        for _ in range(50):
            rclpy.spin_once(self, timeout_sec=0.1)
            try:
                tf = self.tf_buffer.lookup_transform(
                    self.base_frame,
                    self.ee_frame,
                    rclpy.time.Time(),
                )

                pose = PoseStamped()
                pose.header.frame_id = self.base_frame
                pose.pose.position.x = tf.transform.translation.x
                pose.pose.position.y = tf.transform.translation.y
                pose.pose.position.z = tf.transform.translation.z
                pose.pose.orientation = tf.transform.rotation
                return pose

            except Exception:
                pass

        raise RuntimeError(f"Cannot read TF {self.base_frame} -> {self.ee_frame}")

    def print_pose(self):
        pose = self.get_current_pose()
        p = pose.pose.position
        q = pose.pose.orientation

        print()
        print(f"{self.base_frame} -> {self.ee_frame}")
        print(f"x={p.x:.4f}, y={p.y:.4f}, z={p.z:.4f}")
        print(f"qx={q.x:.4f}, qy={q.y:.4f}, qz={q.z:.4f}, qw={q.w:.4f}")
        print()

    def send_position_goal(self, x, y, z):
        if not self.moveit_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("MoveIt /move_action is not available")
            return False

        request = MotionPlanRequest()
        request.group_name = self.group_name
        request.num_planning_attempts = 10
        request.allowed_planning_time = 5.0
        request.max_velocity_scaling_factor = 0.25
        request.max_acceleration_scaling_factor = 0.25

        constraints = Constraints()
        constraints.name = "ee_position_goal"

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.SPHERE
        primitive.dimensions = [0.015]

        region_pose = PoseStamped()
        region_pose.header.frame_id = self.base_frame
        region_pose.pose.position.x = float(x)
        region_pose.pose.position.y = float(y)
        region_pose.pose.position.z = float(z)
        region_pose.pose.orientation.w = 1.0

        volume = BoundingVolume()
        volume.primitives.append(primitive)
        volume.primitive_poses.append(region_pose.pose)

        pc = PositionConstraint()
        pc.header.frame_id = self.base_frame
        pc.link_name = self.ee_frame
        pc.constraint_region = volume
        pc.weight = 1.0

        constraints.position_constraints.append(pc)
        request.goal_constraints.append(constraints)

        options = PlanningOptions()
        options.plan_only = False
        options.look_around = False
        options.replan = False

        goal = MoveGroup.Goal()
        goal.request = request
        goal.planning_options = options

        self.get_logger().info(f"Target: x={x:.3f}, y={y:.3f}, z={z:.3f}")

        future = self.moveit_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error("MoveIt goal rejected")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result

        if result.error_code.val == 1:
            self.get_logger().info("Goal reached")
            return True

        self.get_logger().error(f"MoveIt failed, error_code={result.error_code.val}")
        return False

    def send_home(self):
        if not self.moveit_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error("MoveIt /move_action is not available")
            return False

        request = MotionPlanRequest()
        request.group_name = self.group_name
        request.num_planning_attempts = 5
        request.allowed_planning_time = 5.0
        request.max_velocity_scaling_factor = 0.3
        request.max_acceleration_scaling_factor = 0.3

        constraints = Constraints()
        constraints.name = "home"

        for name in self.joint_names:
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = 0.0
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)

        request.goal_constraints.append(constraints)

        options = PlanningOptions()
        options.plan_only = False

        goal = MoveGroup.Goal()
        goal.request = request
        goal.planning_options = options

        future = self.moveit_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()
        if goal_handle is None or not goal_handle.accepted:
            self.get_logger().error("Home goal rejected")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result

        if result.error_code.val == 1:
            self.get_logger().info("Home reached")
            return True

        self.get_logger().error(f"Home failed, error_code={result.error_code.val}")
        return False

    def run(self):
        print()
        print("End-effector teleop for link_5")
        print("Commands:")
        print("  w : X +")
        print("  s : X -")
        print("  a : Y +")
        print("  d : Y -")
        print("  q : Z +")
        print("  e : Z -")
        print("  p : print pose")
        print("  h : home")
        print("  x : exit")
        print()

        while rclpy.ok():
            cmd = input("cmd> ").strip().lower()

            if cmd == "x":
                return

            if cmd == "p":
                self.print_pose()
                continue

            if cmd == "h":
                self.send_home()
                continue

            if cmd not in ["w", "s", "a", "d", "q", "e"]:
                print("Unknown command")
                continue

            pose = self.get_current_pose()
            p = pose.pose.position

            x = p.x
            y = p.y
            z = p.z

            if cmd == "w":
                x += self.step
            elif cmd == "s":
                x -= self.step
            elif cmd == "a":
                y += self.step
            elif cmd == "d":
                y -= self.step
            elif cmd == "q":
                z += self.step
            elif cmd == "e":
                z -= self.step

            self.send_position_goal(x, y, z)


def main():
    rclpy.init()
    node = EndEffectorKeyboardTeleop()

    try:
        node.run()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
