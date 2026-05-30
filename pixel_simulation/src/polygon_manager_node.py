#!/usr/bin/env python3
"""
PolygonManagerNode - Polygon Storage and Retrieval Manager

DESCRIPTION:
───────────────────────────────────────────────────────────────────
Manages persistent polygon storage and retrieval from YAML file.
Provides ROS2 services for listing and retrieving polygons.

STORAGE FORMAT:
───────────────────────────────────────────────────────────────────
Polygons are stored in YAML format with the structure:

  polygons:
    Field_1:
      - [0.99, -3.44, 0.0]
      - [-2.41, -3.54, 0.0]
      - [-2.31, -0.65, 0.0]
      - [0.60, -1.07, 0.0]
    Field_2:
      - [0.69, -3.77, 0.0]
      - ...

SERVICES PROVIDED:
───────────────────────────────────────────────────────────────────
  /polygon_manager/list_polygons (ListPolygons)
    Returns list of all available polygon names
    
  /polygon_manager/get_polygon (GetPolygon)
    Retrieves point array for a specific polygon
    Input: polygon_name (string)
    Output: found (bool), polygon (geometry_msgs/Point[])

PARAMETER:
───────────────────────────────────────────────────────────────────
  yaml_path (string): Path to polygon YAML file
    (default: ~/polygons.yaml)
    (can be overridden in launch file)
"""

import os
import yaml
from pathlib import Path

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from polygon_interfaces.srv import ListPolygons, GetPolygon


class PolygonManagerNode(Node):
    """
    Manages persistent polygon storage and retrieval.
    
    Services:
    - /polygon_manager/list_polygons: List all available polygon names
    - /polygon_manager/get_polygon: Get points for a specific polygon
    """

    def __init__(self):
        super().__init__('polygon_manager_node')

        # Declare parameter for YAML path
        self.declare_parameter('yaml_path', '~/polygons.yaml')
        yaml_path = self.get_parameter('yaml_path').value
        self.yaml_path = Path(yaml_path).expanduser()

        # Dictionary to hold loaded polygons
        self.polygons = {}

        # Load polygons from YAML
        self.load_polygons()

        # Create services
        self.list_service = self.create_service(
            ListPolygons,
            '/polygon_manager/list_polygons',
            self.list_polygons_callback
        )

        self.get_service = self.create_service(
            GetPolygon,
            '/polygon_manager/get_polygon',
            self.get_polygon_callback
        )

        self.get_logger().info(
            f'PolygonManagerNode initialized. YAML path: {self.yaml_path}'
        )
        self.get_logger().info(
            f'Loaded {len(self.polygons)} polygons: {list(self.polygons.keys())}'
        )

    def load_polygons(self):
        """Load polygons from YAML file."""
        if not self.yaml_path.exists():
            self.get_logger().warn(
                f'Polygon YAML file not found: {self.yaml_path}. Creating empty dict.'
            )
            self.polygons = {}
            return

        try:
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f)

            if data is None or 'polygons' not in data:
                self.get_logger().warn(
                    f'No "polygons" key found in {self.yaml_path}. Starting with empty dict.'
                )
                self.polygons = {}
                return

            self.polygons = {}
            for poly_name, points_list in data['polygons'].items():
                if isinstance(points_list, list):
                    self.polygons[poly_name] = points_list
                    self.get_logger().debug(
                        f'Loaded polygon "{poly_name}" with {len(points_list)} points'
                    )

            self.get_logger().info(
                f'Successfully loaded {len(self.polygons)} polygons from {self.yaml_path}'
            )

        except yaml.YAMLError as e:
            self.get_logger().error(f'YAML parsing error: {e}')
            self.polygons = {}
        except Exception as e:
            self.get_logger().error(f'Error loading polygons: {e}')
            self.polygons = {}

    def list_polygons_callback(self, request, response):
        """Handle ListPolygons service request."""
        response.polygon_names = list(self.polygons.keys())
        self.get_logger().debug(
            f'ListPolygons service called. Returning {len(response.polygon_names)} polygons'
        )
        return response

    def get_polygon_callback(self, request, response):
        """Handle GetPolygon service request."""
        polygon_name = request.polygon_name
        self.get_logger().debug(f'GetPolygon service called for: {polygon_name}')

        if polygon_name not in self.polygons:
            self.get_logger().warn(f'Polygon "{polygon_name}" not found')
            response.found = False
            return response

        # Convert polygon points to geometry_msgs/Point
        points_data = self.polygons[polygon_name]
        response.polygon = []

        for point_data in points_data:
            if isinstance(point_data, (list, tuple)) and len(point_data) >= 2:
                point = Point()
                point.x = float(point_data[0])
                point.y = float(point_data[1])
                point.z = float(point_data[2]) if len(point_data) > 2 else 0.0
                response.polygon.append(point)

        response.found = True
        self.get_logger().info(
            f'GetPolygon returned "{polygon_name}" with {len(response.polygon)} points'
        )
        return response


def main(args=None):
    rclpy.init(args=args)
    node = PolygonManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
