#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse
from rclpy.executors import MultiThreadedExecutor

from geometry_msgs.msg import PointStamped, Point
from momentum_polygon.action import RecordPolygon

import yaml
import os
import time
import threading


# =====================================================
# 🔧 CUSTOM YAML REPRESENTATION FOR [x, y]
# =====================================================
class FlowList(list):
    pass


def flow_list_representer(dumper, data):
    return dumper.represent_sequence(
        'tag:yaml.org,2002:seq',
        data,
        flow_style=True
    )


yaml.add_representer(FlowList, flow_list_representer)


class PolygonRecorderServer(Node):

    def __init__(self):
        super().__init__('polygon_recorder_server')

        # =====================================================
        # YAML path (already fixed by you)
        # =====================================================
        workspace = os.environ.get('ROS_WORKSPACE')
        if workspace is None:
            raise RuntimeError(
                'ROS_WORKSPACE not set\n'
                'export ROS_WORKSPACE=~/pixel_ws'
            )

        self.yaml_path = os.path.join(
            workspace,
            'src',
            'momentum_polygon',
            'config',
            'polygons.yaml'
        )

        self.get_logger().info(f'Polygon YAML path: {self.yaml_path}')

        # Action server
        self._action_server = ActionServer(
            self,
            RecordPolygon,
            'record_polygon',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback
        )

        # RViz clicked point subscriber
        self.subscription = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.point_callback,
            10
        )

        self.recording_active = False
        self.user_done = False
        self.points = []

        self.get_logger().info('Polygon Recorder Action Server started')
        self.get_logger().info('Waiting for /clicked_point from RViz')

    # ================= ACTION CALLBACKS =================

    def goal_callback(self, goal_request):
        self.get_logger().info(
            f"Started recording polygon '{goal_request.polygon_name}'"
        )
        return GoalResponse.ACCEPT

    def execute_callback(self, goal_handle):
        self.recording_active = True
        self.user_done = False
        self.points = []

        polygon_name = goal_handle.request.polygon_name
        feedback = RecordPolygon.Feedback()

        threading.Thread(
            target=self.wait_for_user_confirmation,
            daemon=True
        ).start()

        self.get_logger().info(
            'Click points in RViz. Type "yes" in terminal when done.'
        )

        while rclpy.ok():
            feedback.points_recorded = len(self.points)
            goal_handle.publish_feedback(feedback)

            if self.user_done:

                if len(self.points) < 3:
                    self.get_logger().warn(
                        f'Only {len(self.points)} point(s). '
                        'At least 3 required.'
                    )
                    self.user_done = False
                    continue

                self.recording_active = False
                self.save_polygon(polygon_name, self.points)

                result = RecordPolygon.Result()
                result.success = True
                result.message = (
                    f'Polygon saved successfully with {len(self.points)} points'
                )

                result.polygon_points = []
                for pt in self.points:
                    p = Point()
                    p.x = float(pt[0])
                    p.y = float(pt[1])
                    p.z = 0.0
                    result.polygon_points.append(p)

                goal_handle.succeed()
                return result

            time.sleep(0.1)

        goal_handle.abort()
        result = RecordPolygon.Result()
        result.success = False
        result.message = 'Node shutdown'
        return result

    # ================= SUBSCRIBER =================

    def point_callback(self, msg):
        if not self.recording_active:
            return

        self.points.append([msg.point.x, msg.point.y])
        count = len(self.points)

        self.get_logger().info(
            f"Point {count} recorded: "
            f"({msg.point.x:.2f}, {msg.point.y:.2f})"
        )
        self.get_logger().info(f"Total points so far: {count}")
        self.get_logger().info(
            'Type "yes" in the terminal if you are done adding points'
        )

    # ================= TERMINAL INPUT =================

    def wait_for_user_confirmation(self):
        while self.recording_active and rclpy.ok():
            user_input = input(
                f'Are you done? (yes/no) — points: {len(self.points)}: '
            ).strip()

            if user_input.lower() == 'yes':
                self.user_done = True
                return

    # ================= YAML SAVE (FIXED FOR REAL) =================

    def save_polygon(self, name, points):
        data = {}

        if os.path.exists(self.yaml_path):
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f) or {}

        data.setdefault('polygons', {})

        # Close polygon
        closed = list(points)
        if closed[0] != closed[-1]:
            closed.append(closed[0])

        # ✅ FORCE FLOW STYLE FOR EACH [x, y]
        data['polygons'][name] = [
            FlowList([round(p[0], 6), round(p[1], 6)])
            for p in closed
        ]

        os.makedirs(os.path.dirname(self.yaml_path), exist_ok=True)
        with open(self.yaml_path, 'w') as f:
            yaml.dump(
                data,
                f,
                sort_keys=False,
                default_flow_style=False
            )

        self.get_logger().info(
            f"Polygon '{name}' saved with {len(closed)} points"
        )


def main(args=None):
    rclpy.init(args=args)

    node = PolygonRecorderServer()

    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
