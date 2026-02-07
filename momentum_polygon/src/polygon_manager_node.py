#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import yaml
import os

from polygon_interfaces.srv import GetPolygon


class PolygonServiceProvider(Node):

    def __init__(self):
        super().__init__('polygon_service_provider')

        workspace = os.environ.get('ROS_WORKSPACE')
        if not workspace:
            raise RuntimeError(
                'ROS_WORKSPACE not set. Example:\n'
                'export ROS_WORKSPACE=~/pixel_ws'
            )

        self.yaml_path = os.path.join(
            workspace,
            'src',
            'momentum_polygon',
            'config',
            'polygons.yaml'
        )

        self.polygons = {}
        self.load_polygons()

        self.create_service(
            GetPolygon,
            'polygon_manager/get_polygon',
            self.get_polygon_cb
        )

        self.get_logger().info('Polygon Service Provider ready')

    def load_polygons(self):
        if not os.path.exists(self.yaml_path):
            self.get_logger().warn('Polygon YAML not found')
            return

        with open(self.yaml_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        for name, pts in data.get('polygons', {}).items():
            self.polygons[name] = pts

        self.get_logger().info(
            f'Loaded polygons: {list(self.polygons.keys())}'
        )

    def get_polygon_cb(self, request, response):
        name = request.polygon_name

        if name not in self.polygons:
            response.found = False
            return response

        response.found = True
        response.xs = [p[0] for p in self.polygons[name]]
        response.ys = [p[1] for p in self.polygons[name]]

        return response


def main():
    rclpy.init()
    node = PolygonServiceProvider()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
