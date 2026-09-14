#!/usr/bin/python3

from os.path import join
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # Locate the simulation package and the shared navigation package.
    pixel_bot_path = get_package_share_directory("pixel_simulation")
    titan_nav_path = get_package_share_directory("titan_nav")

    # Keep the simulation map configurable from the command line.
    declare_map_arg = DeclareLaunchArgument(
        "map",
        default_value=join(pixel_bot_path, "maps", "warehouse_map.yaml"),
        description="Full path to map file"
    )

    declare_variant_arg = DeclareLaunchArgument(
        "variant",
        default_value="lidar_only",
        description="Sensor setup used by the shared Titan navigation config",
    )

    pixel_simulation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(pixel_bot_path, "launch", "bringup_sim.launch.py")
        )
    )

    # Use the same Nav2 configuration for simulation and the real robot.
    # The shared launcher selects simulation settings with mode:=sim.
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(titan_nav_path, "launch", "navigation.launch.py")
        ),
        launch_arguments={
            "map": LaunchConfiguration("map"),
            "mode": "sim",
            "variant": LaunchConfiguration("variant"),
        }.items()
    )

    

    return LaunchDescription([
        declare_map_arg,
        declare_variant_arg,
        pixel_simulation,
        navigation_launch,
        
    ])
