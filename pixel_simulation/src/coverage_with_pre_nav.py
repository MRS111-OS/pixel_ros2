#!/usr/bin/env python3

from enum import Enum
import time

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import Point32, Polygon, PoseStamped
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
from opennav_coverage_msgs.action import NavigateCompleteCoverage

import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.duration import Duration


class TaskResult(Enum):
    UNKNOWN = 0
    SUCCEEDED = 1
    CANCELED = 2
    FAILED = 3


class CoverageNavigator(Node):

    def __init__(self):
        super().__init__('coverage_pre_nav')

        # Action Clients
        self.nav_to_pose_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose')

        self.coverage_client = ActionClient(
            self, NavigateCompleteCoverage, 'navigate_complete_coverage')

        self.goal_handle = None
        self.result_future = None
        self.status = None
        self.feedback = None

    # -------------------------------------------------
    # Lifecycle Wait
    # -------------------------------------------------
    def wait_until_active(self, node_name):
        self.get_logger().info(f"Waiting for {node_name} to become active...")

        client = self.create_client(GetState, f'{node_name}/get_state')
        while not client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for lifecycle service...")

        req = GetState.Request()
        state = 'unknown'

        while state != 'active':
            future = client.call_async(req)
            rclpy.spin_until_future_complete(self, future)

            if future.result():
                state = future.result().current_state.label
                self.get_logger().info(f"{node_name} state: {state}")
            time.sleep(1)

    # -------------------------------------------------
    # Navigate to first pose
    # -------------------------------------------------
    def go_to_pose(self, x, y):

        self.get_logger().info("Waiting for NavigateToPose server...")

        while not self.nav_to_pose_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info("NavigateToPose not available...")

        goal = NavigateToPose.Goal()

        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.orientation.w = 1.0

        goal.pose = pose

        self.get_logger().info(f"Navigating to first corner: ({x}, {y})")

        send_goal_future = self.nav_to_pose_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_goal_future)

        goal_handle = send_goal_future.result()

        if not goal_handle.accepted:
            self.get_logger().error("NavigateToPose goal rejected!")
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        status = result_future.result().status

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info("Reached first pose successfully!")
            return True
        else:
            self.get_logger().error(f"Failed to reach first pose. Status: {status}")
            return False

    # -------------------------------------------------
    # Convert list to Polygon
    # -------------------------------------------------
    def to_polygon(self, points):
        poly = Polygon()
        for p in points:
            pt = Point32()
            pt.x = p[0]
            pt.y = p[1]
            pt.z = 0.0
            poly.points.append(pt)
        return poly

    # -------------------------------------------------
    # Send Coverage Goal
    # -------------------------------------------------
    def start_coverage(self, field):

        self.get_logger().info("Waiting for Coverage Action Server...")

        while not self.coverage_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info("Coverage server not available...")

        goal = NavigateCompleteCoverage.Goal()
        goal.frame_id = 'map'
        goal.polygons.append(self.to_polygon(field))

        self.get_logger().info("Sending coverage goal...")

        send_goal_future = self.coverage_client.send_goal_async(
            goal, self.feedback_callback)

        rclpy.spin_until_future_complete(self, send_goal_future)
        self.goal_handle = send_goal_future.result()

        if not self.goal_handle.accepted:
            self.get_logger().error("Coverage goal rejected!")
            return False

        self.get_logger().info("Coverage goal accepted!")

        self.result_future = self.goal_handle.get_result_async()
        return True

    def feedback_callback(self, msg):
        self.feedback = msg.feedback

    def wait_for_coverage(self):
        while rclpy.ok():
            rclpy.spin_once(self, timeout_sec=0.1)

            if self.result_future.done():
                status = self.result_future.result().status

                if status == GoalStatus.STATUS_SUCCEEDED:
                    self.get_logger().info("Coverage completed successfully!")
                else:
                    self.get_logger().error(f"Coverage failed with status: {status}")
                break

            if self.feedback:
                eta = Duration.from_msg(
                    self.feedback.estimated_time_remaining
                ).nanoseconds / 1e9
                self.get_logger().info(f"ETA: {eta:.1f} sec")

            time.sleep(1)


# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    rclpy.init()

    navigator = CoverageNavigator()

    # Wait until BT navigator is active
    navigator.wait_until_active('bt_navigator')

    # Your 4-click polygon (closed)
    field = [
        [-2.6147, -5.6126],
        [1.2165, -5.4761],
        [1.0239, -1.9978],
        [-2.8351, -1.8634],
        [-2.6147, -5.6126]
    ]

    first_x = field[0][0]
    first_y = field[0][1]

    # Step 1: Go to first corner
    if navigator.go_to_pose(first_x, first_y):

        # Step 2: Start coverage
        if navigator.start_coverage(field):
            navigator.wait_for_coverage()

    rclpy.shutdown()


if __name__ == '__main__':
    main()