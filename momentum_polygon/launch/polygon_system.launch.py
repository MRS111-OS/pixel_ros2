#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    # Get package directory
    pkg_dir = get_package_share_directory('momentum_polygon')
    
    # Default YAML path
    default_yaml = os.path.join(pkg_dir, 'config', 'polygons.yaml')
    
    # Launch arguments
    yaml_path_arg = DeclareLaunchArgument(
        'yaml_path',
        default_value=default_yaml,
        description='Path to polygons.yaml file'
    )
    
    yaml_path = LaunchConfiguration('yaml_path')
    
    # Polygon recorder action server
    polygon_recorder_node = Node(
        package='momentum_polygon',
        executable='polygon_recorder_server.py',
        name='polygon_recorder_server',
        output='screen',
        parameters=[{'yaml_path': yaml_path}]
    )
    
    # Polygon manager node
    polygon_manager_node = Node(
        package='momentum_polygon',
        executable='polygon_manager_node.py',
        name='polygon_manager_node',
        output='screen',
        parameters=[{'yaml_path': yaml_path}]
    )
    
    return LaunchDescription([
        yaml_path_arg,
        polygon_recorder_node,
        polygon_manager_node,
    ])
