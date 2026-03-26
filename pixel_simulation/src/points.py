#!/usr/bin/env python3

import math
import time

from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Point, Point32, PointStamped, Polygon
from lifecycle_msgs.srv import GetState
from opennav_coverage_msgs.action import NavigateCompleteCoverage
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

        self.clicked_point_sub = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.clicked_point_callback,
            10,
        )

        self.marker_pub = self.create_publisher(Marker, '/clicked_polygon_marker', 10)
        self.coverage_client = ActionClient(
            self,
            NavigateCompleteCoverage,
            'navigate_complete_coverage',
        )

        self.bt_xml = (
            get_package_share_directory('pixel_simulation')
            + '/config/clicked_complete_coverage.xml'
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
            self.send_coverage_goal()

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

    def send_coverage_goal(self):
        if not self.coverage_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('navigate_complete_coverage action server not available.')
            return

        ordered_points = self.order_polygon_points(self.clicked_points)
        area = self.polygon_area(ordered_points)
        if area < self.min_polygon_area:
            self.get_logger().error(
                f'Polygon area too small ({area:.3f} m^2). Click a larger polygon and try again.'
            )
            self.reset_points()
            return

        closed_points = list(ordered_points)
        if closed_points[0] != closed_points[-1]:
            closed_points.append(closed_points[0])

        polygon = Polygon()
        for x, y in closed_points:
            pt = Point32()
            pt.x = x
            pt.y = y
            pt.z = 0.0
            polygon.points.append(pt)

        goal = NavigateCompleteCoverage.Goal()
        goal.frame_id = self.frame_id
        goal.polygons.append(polygon)
        goal.behavior_tree = self.bt_xml

        self.get_logger().info('Sending 4-point polygon to navigate_complete_coverage...')
        send_goal_future = self.coverage_client.send_goal_async(goal)
        send_goal_future.add_done_callback(self.goal_response_callback)
        self.goal_sent = True

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle or not goal_handle.accepted:
            self.get_logger().error('Coverage goal was rejected.')
            self.goal_sent = False
            return

        self.get_logger().info('Coverage goal accepted.')
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.goal_result_callback)

    def goal_result_callback(self, future):
        result = future.result()
        if result is None:
            self.get_logger().error('Coverage goal result failed.')
            self.goal_sent = False
            return
        self.get_logger().info(f'Coverage finished with status code: {result.status}')
        self.goal_sent = False

    def reset_points(self):
        self.clicked_points = []
        self.goal_sent = False

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
