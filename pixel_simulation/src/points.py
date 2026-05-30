#!/usr/bin/env python3

import math
import time

from action_msgs.msg import GoalStatus
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Point, Point32, PointStamped, PoseStamped, Polygon
from lifecycle_msgs.srv import GetState
from opennav_coverage_msgs.action import ComputeCoveragePath
from opennav_coverage_msgs.msg import Coordinate, Coordinates
from nav2_msgs.action import NavigateToPose, FollowPath
import rclpy
from rclpy.action import ActionClient
from rclpy.node import Node
from visualization_msgs.msg import Marker


class ClickedPointsCoverageNode(Node):

    def __init__(self):
        super().__init__('clicked_points_coverage_node')

        self.frame_id = 'map'
        self.required_points = 4
        self.min_polygon_area = 0.25
        self.clicked_points = []
        self.goal_sent = False
        self.coverage_nav_path = None  # Store computed path

        self.clicked_point_sub = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.clicked_point_callback,
            10,
        )

        self.marker_pub = self.create_publisher(Marker, '/clicked_polygon_marker', 10)

        # Action clients for the new workflow
        self.compute_coverage_client = ActionClient(
            self,
            ComputeCoveragePath,
            'compute_coverage_path',
        )

        self.navigate_to_pose_client = ActionClient(
            self,
            NavigateToPose,
            'navigate_to_pose',
        )

        self.follow_path_client = ActionClient(
            self,
            FollowPath,
            'follow_path',
        )

        self.create_timer(0.2, self.publish_markers)

        self.wait_for_bt_navigator_active()

        self.get_logger().info(
            'Listening on /clicked_point. Click 4 points in RViz to send coverage polygon.'
        )

    def wait_for_bt_navigator_active(self):
        node_service = 'bt_navigator/get_state'
        state_client = self.create_client(GetState, node_service)

        while not state_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info(f'{node_service} service not available, waiting...')

        req = GetState.Request()
        state = 'unknown'
        while state != 'active':
            future = state_client.call_async(req)
            rclpy.spin_until_future_complete(self, future)
            if future.result() is not None:
                state = future.result().current_state.label
                self.get_logger().info(f'bt_navigator state: {state}')
            time.sleep(1.0)

    def clicked_point_callback(self, msg: PointStamped):
        if self.goal_sent:
            return

        if len(self.clicked_points) >= self.required_points:
            return

        self.clicked_points.append((float(msg.point.x), float(msg.point.y)))
        self.get_logger().info(
            f'Point {len(self.clicked_points)}/{self.required_points}: '
            f'x={msg.point.x:.3f}, y={msg.point.y:.3f}'
        )

        if len(self.clicked_points) == self.required_points:
            self.compute_coverage_path_goal()

    def publish_markers(self):
        self.publish_points_marker()
        self.publish_line_marker()

    def publish_points_marker(self):
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'clicked_polygon'
        marker.id = 0
        marker.type = Marker.SPHERE_LIST
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.18
        marker.scale.y = 0.18
        marker.scale.z = 0.18
        marker.color.r = 0.0
        marker.color.g = 1.0
        marker.color.b = 0.2
        marker.color.a = 1.0

        marker.points = [self.to_point(x, y) for x, y in self.clicked_points]
        self.marker_pub.publish(marker)

    def publish_line_marker(self):
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = self.get_clock().now().to_msg()
        marker.ns = 'clicked_polygon'
        marker.id = 1
        marker.type = Marker.LINE_STRIP
        marker.action = Marker.ADD
        marker.pose.orientation.w = 1.0
        marker.scale.x = 0.05
        marker.color.r = 1.0
        marker.color.g = 0.3
        marker.color.b = 0.0
        marker.color.a = 1.0

        display_points = self.clicked_points
        if len(self.clicked_points) == self.required_points:
            display_points = self.order_polygon_points(self.clicked_points)

        line_points = [self.to_point(x, y) for x, y in display_points]
        if len(line_points) > 2:
            line_points.append(self.to_point(display_points[0][0], display_points[0][1]))
        marker.points = line_points

        self.marker_pub.publish(marker)

    def compute_coverage_path_goal(self):
        """Step 1: Send ComputeCoveragePath action to generate the coverage path."""
        if not self.compute_coverage_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('compute_coverage_path action server not available.')
            return

        ordered_points = self.order_polygon_points(self.clicked_points)
        area = self.polygon_area(ordered_points)
        if area < self.min_polygon_area:
            self.get_logger().error(
                f'Polygon area too small ({area:.3f} m^2). Click a larger polygon and try again.'
            )
            self.reset_points()
            return

        # Build Coordinates message for the polygon
        coords = Coordinates()

        closed_points = list(ordered_points)

        # Repeat first point at the end
        if closed_points[0] != closed_points[-1]:
            closed_points.append(closed_points[0])

        for x, y in closed_points:
            c = Coordinate()
            c.axis1 = float(x)
            c.axis2 = float(y)
            coords.coordinates.append(c)

            self.get_logger().info(
                f"Sending {len(coords.coordinates)} coordinates"
            )

            for c in coords.coordinates:
                self.get_logger().info(
                    f"({c.axis1:.3f}, {c.axis2:.3f})"
                )

        # Build ComputeCoveragePath goal
        goal = ComputeCoveragePath.Goal()
        goal.frame_id = self.frame_id
        goal.polygons.append(coords)
        goal.generate_headland = False
        goal.generate_route = True
        goal.generate_path = True

        self.get_logger().info('Sending 4-point polygon to compute_coverage_path...')
        send_goal_future = self.compute_coverage_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.compute_goal_response)
        self.goal_sent = True

    def compute_goal_response(self, future):
        """Handle ComputeCoveragePath goal acceptance."""
        goal_handle = future.result()
        if not goal_handle or not goal_handle.accepted:
            self.get_logger().error('Compute coverage goal was rejected.')
            self.goal_sent = False
            return

        self.get_logger().info('Compute coverage goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.compute_result_callback)

    def compute_result_callback(self, future):

        result_msg = future.result()

        if result_msg is None:
            self.get_logger().error(
                'Compute coverage result failed.'
            )
            self.goal_sent = False
            return

        result = result_msg.result

        self.get_logger().info(
            f'error_code={result.error_code}'
        )

        self.get_logger().info(
            f'poses={len(result.nav_path.poses)}'
        )

        self.get_logger().info(
            f'Coverage path computed with {len(result.nav_path.poses)} poses.'
        )

        self.coverage_nav_path = result.nav_path

        if len(self.coverage_nav_path.poses) == 0:
            self.get_logger().error('Coverage path is empty.')
            self.goal_sent = False
            return
        
        start_pose = self.coverage_nav_path.poses[0]
        start_pose.header.frame_id = self.frame_id
        start_pose.header.stamp = self.get_clock().now().to_msg()
        

        if not start_pose.header.frame_id:
            start_pose.header.frame_id = self.frame_id

        start_pose.header.stamp = self.get_clock().now().to_msg()

        self.get_logger().info(
            f"Coverage start frame={start_pose.header.frame_id}"
        )

        self.get_logger().info(
            f"Coverage start x={start_pose.pose.position.x:.3f}, "
            f"y={start_pose.pose.position.y:.3f}"
        )

        self.send_navigate_to_pose(start_pose)

    def send_navigate_to_pose(self, target_pose):
        """Step 3: Navigate to the start of the coverage path."""
        if not self.navigate_to_pose_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('navigate_to_pose action server not available.')
            self.goal_sent = False
            return

        self.get_logger().info(
            f'NavigateToPose target frame={target_pose.header.frame_id}'
        )

        self.get_logger().info(
            f'NavigateToPose target x={target_pose.pose.position.x:.3f}, '
            f'y={target_pose.pose.position.y:.3f}'
        )

        goal = NavigateToPose.Goal()
        goal.pose = target_pose

        self.get_logger().info(
            f'Sending NavigateToPose goal to ({target_pose.pose.position.x:.3f}, '
            f'{target_pose.pose.position.y:.3f})'
        )
        send_goal_future = self.navigate_to_pose_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.navigate_goal_response)

    def navigate_goal_response(self, future):
        """Handle NavigateToPose goal acceptance."""
        goal_handle = future.result()
        if not goal_handle or not goal_handle.accepted:
            self.get_logger().error('Navigate to pose goal was rejected.')
            self.goal_sent = False
            return

        self.get_logger().info('Navigate to pose goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.navigate_result_callback)

    def navigate_result_callback(self, future):
        """
        Step 4: After reaching the start pose, send FollowPath along the coverage path.
        """
        result_msg = future.result()

        self.get_logger().info(
            f'NavigateToPose status = {result_msg.status}'
        )

        if result_msg.status != GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().error(
                f'NavigateToPose failed with status {result_msg.status}'
            )
            self.goal_sent = False
            return

        self.get_logger().info('✓ Robot reached first point! Starting coverage path following.')

        # Send FollowPath goal with the computed coverage path
        self.send_follow_path()

    def send_follow_path(self):
        """Step 5: Follow the computed coverage path."""
        if not self.follow_path_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('follow_path action server not available.')
            self.goal_sent = False
            return

        if self.coverage_nav_path is None:
            self.get_logger().error('No coverage path available.')
            self.goal_sent = False
            return

        goal = FollowPath.Goal()
        goal.path = self.coverage_nav_path
        goal.controller_id = 'FollowPath'
        goal.goal_checker_id = ''

        self.get_logger().info('Sending FollowPath goal for coverage traversal.')
        send_goal_future = self.follow_path_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.follow_goal_response)

    def follow_goal_response(self, future):
        """Handle FollowPath goal acceptance."""
        goal_handle = future.result()
        if not goal_handle or not goal_handle.accepted:
            self.get_logger().error('Follow path goal was rejected.')
            self.goal_sent = False
            return

        self.get_logger().info('Follow path goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.follow_result_callback)

    def follow_result_callback(self, future):
        """Handle FollowPath completion."""
        result_msg = future.result()

        self.get_logger().info(
            f'FollowPath status = {result_msg.status}'
        )

        if result_msg.status != GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().error(
                f'FollowPath failed with status {result_msg.status}'
            )
        else:
            self.get_logger().info('✓ Coverage path traversal complete!')

        self.goal_sent = False
        self.reset_points()

    def reset_points(self):
        self.clicked_points = []
        self.goal_sent = False
        self.coverage_nav_path = None

    @staticmethod
    def order_polygon_points(points):
        centroid_x = sum(p[0] for p in points) / len(points)
        centroid_y = sum(p[1] for p in points) / len(points)
        return sorted(
            points,
            key=lambda p: math.atan2(p[1] - centroid_y, p[0] - centroid_x)
        )

    @staticmethod
    def polygon_area(points):
        area = 0.0
        for i in range(len(points)):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % len(points)]
            area += (x1 * y2) - (x2 * y1)
        return abs(area) * 0.5

    @staticmethod
    def to_point(x: float, y: float) -> Point:
        p = Point()
        p.x = x
        p.y = y
        p.z = 0.03
        return p


def main(args=None):
    rclpy.init(args=args)
    node = ClickedPointsCoverageNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
