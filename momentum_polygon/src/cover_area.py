#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from geometry_msgs.msg import Polygon, Point32
from opennav_coverage_msgs.action import NavigateCompleteCoverage
from ament_index_python.packages import get_package_share_directory
import yaml
import os
import sys


class CoverAreaClient(Node):
    """
    Client node that sends polygon to opennav_coverage for coverage navigation.
    Usage: ros2 run momentum_polygon cover_area.py <polygon_name>
    """

    def __init__(self, polygon_name):
        super().__init__('cover_area_client')
        
        self.polygon_name = polygon_name
        
        # Load polygons from YAML
        self.polygons = self.load_polygons()
        
        # Action client for opennav_coverage
        self._action_client = ActionClient(
            self,
            NavigateCompleteCoverage,
            'navigate_complete_coverage'
        )
        
        self.get_logger().info(f'Waiting for opennav_coverage action server...')

    def load_polygons(self):
        """Load polygons from YAML file"""
        try:
            # Try source directory first (for development)
            source_yaml = os.path.normpath(
                os.path.join(os.path.dirname(__file__), '..', 'config', 'polygons.yaml')
            )
            if os.path.exists(source_yaml):
                yaml_path = source_yaml
            else:
                # Fallback to installed location
                pkg_share = get_package_share_directory('momentum_polygon')
                yaml_path = os.path.join(pkg_share, 'config', 'polygons.yaml')
        except:
            yaml_path = os.path.normpath(
                os.path.join(os.path.dirname(__file__), '..', 'config', 'polygons.yaml')
            )
        
        self.get_logger().info(f'Loading polygons from: {yaml_path}')
        
        if not os.path.exists(yaml_path):
            self.get_logger().error(f'YAML file not found: {yaml_path}')
            return {}
        
        try:
            with open(yaml_path, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            polygons = {}
            polygons_data = data.get('polygons', {})
            
            if polygons_data and isinstance(polygons_data, dict):
                for name, pts in polygons_data.items():
                    if pts and isinstance(pts, list):
                        polygons[name] = [[float(p[0]), float(p[1])] for p in pts]
            
            self.get_logger().info(f'Loaded {len(polygons)} polygons: {list(polygons.keys())}')
            return polygons
        except Exception as e:
            self.get_logger().error(f'Error loading polygons: {str(e)}')
            return {}

    def get_polygon_as_geometry_polygon(self, polygon_name):
        """Convert polygon to geometry_msgs/Polygon"""
        if polygon_name not in self.polygons:
            return None
        
        poly = Polygon()
        for pt in self.polygons[polygon_name]:
            point = Point32()
            point.x = float(pt[0])
            point.y = float(pt[1])
            point.z = 0.0
            poly.points.append(point)
        
        return poly

    def send_goal(self):
        """Send the polygon to opennav_coverage"""
        # Get polygon
        polygon = self.get_polygon_as_geometry_polygon(self.polygon_name)
        
        if polygon is None:
            self.get_logger().error(f'Polygon "{self.polygon_name}" not found!')
            self.get_logger().info(f'Available polygons: {list(self.polygons.keys())}')
            return False
        
        # Wait for action server
        if not self._action_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Action server not available!')
            return False
        
        # Create goal
        goal_msg = NavigateCompleteCoverage.Goal()
        goal_msg.polygons = [polygon]  # Array of polygons
        goal_msg.frame_id = 'map'
        goal_msg.field_filepath = ''  # Not using file
        
        self.get_logger().info(f'Sending polygon "{self.polygon_name}" with {len(polygon.points)} points to opennav_coverage')
        
        # Send goal
        self._send_goal_future = self._action_client.send_goal_async(
            goal_msg,
            feedback_callback=self.feedback_callback
        )
        self._send_goal_future.add_done_callback(self.goal_response_callback)
        
        return True

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected!')
            return

        self.get_logger().info('Goal accepted! Coverage navigation started.')
        
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Coverage complete! Error code: {result.error_code}')
        
        # Shutdown after completion
        rclpy.shutdown()

    def feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(
            f'Distance remaining: {feedback.distance_remaining:.2f}m, '
            f'Recoveries: {feedback.number_of_recoveries}'
        )


def main(args=None):
    rclpy.init(args=args)
    
    # Get polygon name from command line
    if len(sys.argv) < 2:
        print('Usage: ros2 run momentum_polygon cover_area.py <polygon_name>')
        print('Example: ros2 run momentum_polygon cover_area.py field1')
        sys.exit(1)
    
    polygon_name = sys.argv[1]
    
    node = CoverAreaClient(polygon_name)
    
    # Send goal
    if node.send_goal():
        rclpy.spin(node)
    else:
        node.get_logger().error('Failed to send goal')
        sys.exit(1)


if __name__ == '__main__':
    main()
