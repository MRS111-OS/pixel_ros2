#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    package_name = 'pixel_simulation'
    package_dir = get_package_share_directory(package_name)
    
    # Polygon YAML file path
    polygon_yaml = os.path.join(
        package_dir,
        'config',
        'polygon.yaml'
    )
    
    # Declare yaml_path argument
    yaml_path_arg = DeclareLaunchArgument(
        'yaml_path',
        default_value=polygon_yaml,
        description='Path to polygons YAML file'
    )
    
    yaml_path = LaunchConfiguration('yaml_path')
    
    # Polygon Manager Node
    polygon_manager = Node(
        package=package_name,
        executable='polygon_manager_node.py',
        name='polygon_manager',
        parameters=[{
            'yaml_path': yaml_path
        }],
        output='screen'
    )
    
    # Polygon Recorder Server Node
    polygon_recorder = Node(
        package=package_name,
        executable='polygon_recorder_server.py',
        name='polygon_recorder',
        parameters=[{
            'yaml_path': yaml_path
        }],
        output='screen'
    )
    
    ld = LaunchDescription()
    
    ld.add_action(yaml_path_arg)
    ld.add_action(polygon_manager)
    ld.add_action(polygon_recorder)
    
    return ld
