#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from geometry_msgs.msg import Point32, Polygon
from opennav_coverage_msgs.action import NavigateCompleteCoverage
from polygon_interfaces.srv import GetPolygon


class CoverageFromPolygon(Node):

    def __init__(self):
        super().__init__('coverage_from_polygon')

        self.poly_client = self.create_client(
            GetPolygon,
            'polygon_manager/get_polygon'
        )

        self.coverage_client = ActionClient(
            self,
            NavigateCompleteCoverage,
            'navigate_complete_coverage'
        )

    def request_polygon(self, polygon_name):
        while not self.poly_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for polygon service...')

        req = GetPolygon.Request()
        req.polygon_name = polygon_name

        future = self.poly_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        return future.result()

    def to_polygon_msg(self, xs, ys):
        poly = Polygon()
        for x, y in zip(xs, ys):
            pt = Point32()
            pt.x = float(x)
            pt.y = float(y)
            poly.points.append(pt)
        return poly

    def send_coverage_goal(self, poly_msg):
        while not self.coverage_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info(
                'Waiting for NavigateCompleteCoverage action server...'
            )

        goal = NavigateCompleteCoverage.Goal()
        goal.frame_id = 'map'
        goal.polygons.append(poly_msg)

        self.get_logger().info(
            f'Sending coverage goal with {len(poly_msg.points)} points'
        )

        self.coverage_client.send_goal_async(goal)


def main():
    rclpy.init()

    node = CoverageFromPolygon()

    polygon_name = 'field1'
    response = node.request_polygon(polygon_name)

    if not response or not response.found:
        node.get_logger().error(f'Polygon "{polygon_name}" not found')
        return

    polygon_msg = node.to_polygon_msg(response.xs, response.ys)
    node.send_coverage_goal(polygon_msg)

    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
