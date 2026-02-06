#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, Polygon, Point32
from ament_index_python.packages import get_package_share_directory
import yaml
import os


class PolygonManagerNode(Node):
    """
    Service provider node that loads polygons from YAML
    and provides them to other nodes via services.
    """

    def __init__(self):
        super().__init__('polygon_manager_node')

        # Default YAML path: <pkg_source>/config/polygons.yaml (for development)
        # Use source directory so changes are persistent across rebuilds
        default_yaml = os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', 'config', 'polygons.yaml')
        )
        self.declare_parameter('yaml_path', default_yaml)
        self.yaml_path = self.get_parameter('yaml_path').value

        self.polygons = {}
        self.load_polygons()

        # Create timer to periodically check for updates
        self.create_timer(2.0, self.check_and_reload)

        self.get_logger().info(f'Polygon Manager started. Loaded {len(self.polygons)} polygons.')

    def load_polygons(self):
        """Load polygons from YAML file"""
        if not os.path.exists(self.yaml_path):
            self.get_logger().warn(f'YAML file not found: {self.yaml_path}')
            self.polygons = {}
            return

        try:
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f) or {}

            self.polygons = {}
            polygons_data = data.get('polygons', {})
            
            # Handle case where polygons: is None or not a dict
            if polygons_data and isinstance(polygons_data, dict):
                for name, pts in polygons_data.items():
                    if pts and isinstance(pts, list):
                        # Store as list of [x, y] for easy conversion
                        self.polygons[name] = [[float(p[0]), float(p[1])] for p in pts]
                
            self.get_logger().info(f'Loaded {len(self.polygons)} polygons: {list(self.polygons.keys())}')
        except Exception as e:
            self.get_logger().error(f'Error loading polygons: {str(e)}')

    def check_and_reload(self):
        """Periodically reload polygons if file has changed"""
        self.load_polygons()

    def get_polygon_as_geometry_polygon(self, polygon_name):
        """
        Get polygon as geometry_msgs/Polygon (used by NavigateCompleteCoverage)
        Returns None if not found
        """
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

    def get_polygon_names(self):
        """Get list of available polygon names"""
        return list(self.polygons.keys())


def main(args=None):
    rclpy.init(args=args)
    node = PolygonManagerNode()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
