#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import PointStamped, Point
from momentum_polygon.action import RecordPolygon
from ament_index_python.packages import get_package_share_directory
import yaml
import os
import time


class PolygonRecorderServer(Node):

    def __init__(self):
        super().__init__('polygon_recorder_server')

        # Default YAML path: <pkg_source>/config/polygons.yaml (for development)
        # Use source directory so changes are persistent across rebuilds
        default_yaml = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', 'config', 'polygons.yaml')
        )
        self.declare_parameter('yaml_path', default_yaml)
        self.yaml_path = self.get_parameter('yaml_path').value

        # Action server
        self._action_server = ActionServer(
            self,
            RecordPolygon,
            'record_polygon',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback
        )

        # Subscribe to RViz clicked points
        self.subscription = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.point_callback,
            10
        )

        self.recording_active = False
        self.points = []

        self.get_logger().info('Polygon Recorder Action Server started')
        self.get_logger().info(f'YAML path: {self.yaml_path}')
        self.get_logger().info('Listening for /clicked_point messages...')

    # ---------------- ACTION CALLBACKS ----------------

    def goal_callback(self, goal_request):
        self.get_logger().info(
            f"Recording polygon '{goal_request.polygon_name}'"
        )
        return GoalResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.recording_active = True
        self.points = []

        polygon_name = goal_handle.request.polygon_name
        feedback = RecordPolygon.Feedback()

        self.get_logger().info('Waiting for 3 points...')

        while rclpy.ok():
            feedback.points_recorded = len(self.points)
            goal_handle.publish_feedback(feedback)

            # ✅ AUTO-FINISH CONDITION
            if len(self.points) >= 3:
                self.recording_active = False

                self.save_polygon(polygon_name, self.points)

                result = RecordPolygon.Result()
                result.success = True
                result.message = f'Polygon saved successfully with {len(self.points)} points'
                
                # Convert points back to geometry_msgs/Point for result
                result.polygon_points = []
                for pt in self.points:
                    p = Point()
                    p.x = float(pt[0])
                    p.y = float(pt[1])
                    p.z = 0.0
                    result.polygon_points.append(p)

                goal_handle.succeed()
                return result

            time.sleep(0.1)  # SAFE because MultiThreadedExecutor is used

        goal_handle.abort()
        result = RecordPolygon.Result()
        result.success = False
        result.message = 'Node shutdown'
        return result

    # ---------------- SUBSCRIBER CALLBACK ----------------

    def point_callback(self, msg):
        if not self.recording_active:
            return

        self.points.append([msg.point.x, msg.point.y])
        self.get_logger().info(
            f"Point {len(self.points)} recorded: "
            f"({msg.point.x:.2f}, {msg.point.y:.2f})"
        )

    # ---------------- YAML SAVE ----------------

    def save_polygon(self, name, points):
        data = {}

        if os.path.exists(self.yaml_path):
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f) or {}

        data.setdefault('polygons', {})

        saved_points = list(points)
        saved_points.append(saved_points[0])  # close polygon

        data['polygons'][name] = [
            [float(p[0]), float(p[1])] for p in saved_points
        ]

        os.makedirs(os.path.dirname(self.yaml_path), exist_ok=True)
        with open(self.yaml_path, 'w') as f:
            yaml.dump(data, f)

        self.get_logger().info(
            f"Polygon '{name}' saved to {self.yaml_path}"
        )


def main(args=None):
    rclpy.init(args=args)

    node = PolygonRecorderServer()

    # ✅ CRITICAL FIX
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
