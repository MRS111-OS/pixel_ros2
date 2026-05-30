#!/usr/bin/env python3

import os
import time
import yaml
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import PointStamped, Point
from polygon_interfaces.action import RecordPolygon


class PolygonRecorderServer(Node):
    """
    Records polygon points from RViz clicks via an action interface.
    Saves recorded polygons to YAML file.

    THREADING ARCHITECTURE:
    ═══════════════════════════════════════════════════════════════
    Uses MultiThreadedExecutor for CONCURRENT execution:
    
    - Thread 1: Executes execute_callback() (action server)
      Runs the long-loop that waits for action cancellation
      
    - Thread 2+: Execute subscriber callbacks (subscriber)
      Processes /clicked_point messages in parallel
    
    WITHOUT MultiThreadedExecutor (single-threaded):
    ─────────────────────────────────────────────────
    The while loop in execute_callback() BLOCKS the executor,
    preventing any subscriber callbacks from running.
    Result: Clicked points are never processed.
    
    WITH MultiThreadedExecutor:
    ──────────────────────────
    Both callbacks can run concurrently in separate threads.
    Result: Subscriber callback processes points while action loop runs.
    ═══════════════════════════════════════════════════════════════

    Action:
    - /record_polygon: RecordPolygon action for recording polygons
    
    Subscriber:
    - /clicked_point: RViz published points (runs in separate thread)
    """

    def __init__(self):
        super().__init__('polygon_recorder_server')

        # Declare parameter for YAML path
        self.declare_parameter('yaml_path', '~/polygons.yaml')
        yaml_path = self.get_parameter('yaml_path').value
        self.yaml_path = Path(yaml_path).expanduser()

        self.get_logger().info(
            f'PolygonRecorderServer initializing with YAML path: {self.yaml_path}'
        )

        # Current recording state
        self.recording = False
        self.current_polygon_name = None
        self.current_points = []

        # Subscribe to clicked points
        self.clicked_point_sub = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.clicked_point_callback,
            10
        )

        self.get_logger().debug('✓ Created subscription to /clicked_point')

        # Create action server
        self._action_server = ActionServer(
            self,
            RecordPolygon,
            '/record_polygon',
            execute_callback=self.execute_callback
        )

        self.get_logger().info('✓ PolygonRecorderServer initialized and ready')
        self.get_logger().info('Listening for /record_polygon action requests')

    def clicked_point_callback(self, msg: PointStamped):
        """
        Callback for /clicked_point subscription.
        
        KEY: This runs in a SEPARATE THREAD when using MultiThreadedExecutor.
        Without MultiThreadedExecutor, this would be BLOCKED while execute_callback's
        while loop runs, so points would never be recorded.
        """
        self.get_logger().debug(
            f'[SUBSCRIBER THREAD] Click received: x={msg.point.x:.2f}, y={msg.point.y:.2f}'
        )

        if not self.recording:
            self.get_logger().debug('[SUBSCRIBER THREAD] Recording not active, ignoring click')
            return

        point_tuple = (msg.point.x, msg.point.y, msg.point.z)
        self.current_points.append(point_tuple)

        if len(self.current_points) >= 4:
            self.get_logger().info("4 points collected, saving polygon")

            self.save_polygon_to_yaml(
                self.current_polygon_name,
                self.current_points
            )

            self.get_logger().info("Polygon saved")

            self.recording = False
        
        self.get_logger().info(
            f'✓ POINT STORED #{len(self.current_points)}: '
            f'x={msg.point.x:.3f}, y={msg.point.y:.3f}, z={msg.point.z:.3f}'
        )

    def execute_callback(self, goal_handle):
        """
        Execute RecordPolygon action.
        
        KEY: This callback runs in a SEPARATE THREAD thanks to MultiThreadedExecutor.
        The while loop below NO LONGER blocks subscriber callbacks.
        """
        goal = goal_handle.request
        self.current_polygon_name = goal.polygon_name

        self.get_logger().info(
            '╔═══════════════════════════════════════════════════════════════╗'
        )
        self.get_logger().info(
            '║  >>> RecordPolygon ACTION STARTED <<<                        ║'
        )
        self.get_logger().info(
            f'║  Polygon: {self.current_polygon_name:<51}║'
        )
        self.get_logger().info(
            '║  Status: Waiting for RViz clicks (in separate thread)       ║'
        )
        self.get_logger().info(
            '║  Action thread and subscriber thread run in parallel!       ║'
        )
        self.get_logger().info(
            '╚═══════════════════════════════════════════════════════════════╝'
        )

        # Reset and start recording
        self.current_points = []
        self.recording = True

        try:
            # Keep recording while action is active
            # THIS LOOP RUNS IN A SEPARATE THREAD
            # Subscriber callbacks can still execute in another thread
            while self.recording:
                # Publish feedback with current point count
                feedback = RecordPolygon.Feedback()
                feedback.points_recorded = len(self.current_points)
                goal_handle.publish_feedback(feedback)

                self.get_logger().debug(
                    f'[ACTION THREAD] Feedback: {feedback.points_recorded} points'
                )

                # Check if action was cancelled by client
                if goal_handle.is_cancel_requested:
                    self.get_logger().info(
                        '>>> RecordPolygon ACTION CANCELLED BY CLIENT <<<"'
                    )
                    goal_handle.canceled()
                    self.recording = False
                    return RecordPolygon.Result()

                # Sleep briefly (yields CPU to other threads)
                time.sleep(0.5)

        except Exception as e:
            self.get_logger().error(f'✗ Error during recording: {e}')
            self.recording = False
            result = RecordPolygon.Result()
            result.success = False
            result.message = f'Recording error: {e}'
            result.polygon_points = []
            goal_handle.succeed()
            return result

        # Recording stopped
        self.recording = False

        self.get_logger().info(
            f'Recording stopped. Total points collected: {len(self.current_points)}'
        )

        # Validate polygon has minimum points
        if len(self.current_points) < 3:
            self.get_logger().warn(
                f'✗ Polygon "{self.current_polygon_name}" has only {len(self.current_points)} points. '
                f'Minimum 3 points required. Not saving.'
            )
            result = RecordPolygon.Result()
            result.success = False
            result.message = f'Minimum 3 points required (got {len(self.current_points)})'
            result.polygon_points = []
            goal_handle.succeed()
            return result

        # Save polygon to YAML
        self.get_logger().info(
            f'Saving polygon "{self.current_polygon_name}" with {len(self.current_points)} points...'
        )

        success = self.save_polygon_to_yaml(
            self.current_polygon_name,
            self.current_points
        )

        if not success:
            self.get_logger().error(f'✗ Failed to save polygon to YAML')
            result = RecordPolygon.Result()
            result.success = False
            result.message = 'Failed to save polygon to YAML'
            result.polygon_points = []
            goal_handle.succeed()
            return result

        # Return success with recorded points
        result = RecordPolygon.Result()
        result.success = True
        result.message = f'Polygon "{self.current_polygon_name}" saved successfully with {len(self.current_points)} points'
        
        # Convert stored points (x, y, z tuples) to geometry_msgs.msg.Point objects
        result.polygon_points = [
            Point(x=float(p[0]), y=float(p[1]), z=float(p[2]))
            for p in self.current_points
        ]

        self.get_logger().info(
            '╔═══════════════════════════════════════════════════════════════╗'
        )
        self.get_logger().info(
            '║  >>> RecordPolygon ACTION SUCCEEDED <<<                      ║'
        )
        self.get_logger().info(
            f'║  Polygon: {self.current_polygon_name:<51}║'
        )
        self.get_logger().info(
            f'║  Points saved: {len(result.polygon_points):<48}║'
        )
        self.get_logger().info(
            '║  File: ~/polygons.yaml                                     ║'
        )
        self.get_logger().info(
            '╚═══════════════════════════════════════════════════════════════╝'
        )

        goal_handle.succeed()
        return result

    def save_polygon_to_yaml(self, polygon_name: str, points: list) -> bool:
        """
        Save polygon to YAML file, merging with existing polygons.
        
        Args:
            polygon_name: Name of the polygon
            points: List of (x, y, z) tuples
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load existing polygons
            existing_data = {}
            if self.yaml_path.exists():
                try:
                    with open(self.yaml_path, 'r') as f:
                        existing_data = yaml.safe_load(f)
                except Exception as e:
                    self.get_logger().warn(f'Could not read existing YAML: {e}')
                    existing_data = {}

            if existing_data is None:
                existing_data = {}

            # Ensure polygons key exists
            if 'polygons' not in existing_data:
                existing_data['polygons'] = {}

            # Add or overwrite polygon
            existing_data['polygons'][polygon_name] = [
                [float(p[0]), float(p[1]), float(p[2])] for p in points
            ]

            # Create directory if needed
            self.yaml_path.parent.mkdir(parents=True, exist_ok=True)

            # Write back to YAML
            with open(self.yaml_path, 'w') as f:
                yaml.dump(existing_data, f, default_flow_style=False)

            self.get_logger().info(
                f'✓ Saved polygon "{polygon_name}" to {self.yaml_path}'
            )
            return True

        except Exception as e:
            self.get_logger().error(f'✗ Error saving polygon to YAML: {e}')
            return False


def main(args=None):
    rclpy.init(args=args)
    
    # Create node
    node = PolygonRecorderServer()
    
    # Use MultiThreadedExecutor instead of single-threaded executor
    # This is CRITICAL for concurrent callback execution
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    
    node.get_logger().info(
        '╔═══════════════════════════════════════════════════════════════╗'
    )
    node.get_logger().info(
        '║  THREADING MODEL: MultiThreadedExecutor ENABLED              ║'
    )
    node.get_logger().info(
        '║  ✓ Action callbacks: Run in Thread Pool                       ║'
    )
    node.get_logger().info(
        '║  ✓ Subscriber callbacks: Run in Thread Pool (in parallel)     ║'
    )
    node.get_logger().info(
        '║  ✓ Result: Clicked points are recorded while action runs!     ║'
    )
    node.get_logger().info(
        '╚═══════════════════════════════════════════════════════════════╝'
    )
    
    try:
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info('Shutting down...')
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
