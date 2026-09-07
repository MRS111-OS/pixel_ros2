#!/usr/bin/python3

from os.path import join
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable, AppendEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    titan_bot_path = get_package_share_directory("pixel_simulation")
    gz_sim_share = get_package_share_directory("ros_gz_sim")

    world_file = LaunchConfiguration("world_file")

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(gz_sim_share, "launch", "gz_sim.launch.py")
        ),
        launch_arguments={
            "gz_args": [world_file, " -r"]
        }.items()
    )

    spawn_titan_bot_node = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            join(titan_bot_path, "launch", "robot_state_publisher.launch.py")
        )
    )

    return LaunchDescription([

        AppendEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=join(titan_bot_path, "worlds")),

        AppendEnvironmentVariable(
        name='IGN_GAZEBO_RESOURCE_PATH',
        value=join(titan_bot_path, "models")),

        DeclareLaunchArgument(
            "world_file",
            default_value=join(titan_bot_path, "worlds", "small_warehouse.world"),
            description="Ignition Gazebo world file"
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true"
        ),
        gz_sim,
        spawn_titan_bot_node
    ])
