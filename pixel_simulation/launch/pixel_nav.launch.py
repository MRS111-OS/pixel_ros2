#!/usr/bin/python3

from os.path import join
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node


def generate_launch_description():

    pixel_bot_path = get_package_share_directory("pixel_simulation")
    pixel_desc = get_package_share_directory("titan_description")
    nav2_bringup_dir = get_package_share_directory("nav2_bringup")

    declare_map_arg = DeclareLaunchArgument(
        "map",
        default_value=join(pixel_bot_path, "maps", "warehouse_map.yaml"),
        description="Full path to map file"
    )

    pixel_simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(pixel_bot_path, "launch", "bringup_sim.launch.py")
        )
    )

    nav2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(nav2_bringup_dir, "launch", "bringup_launch.py")
        ),
        launch_arguments={
            "map": LaunchConfiguration("map"),
            "use_sim_time": "true",
            "rviz": "false"
        }.items()
    )

    

    return LaunchDescription([
        declare_map_arg,
        pixel_simulation,
        nav2_launch,
        
    ])