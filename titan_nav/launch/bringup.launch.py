#!/usr/bin/python3

from os.path import join, dirname

from pygraphviz import Node
from launch_ros.actions import Node

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable
)
from launch.substitutions import LaunchConfiguration, EnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource

from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    # /home/.../install/titan_nav/share/titan_nav
    titan_pkg_share = get_package_share_directory("titan_nav")

    # /home/.../install/titan_nav
    titan_prefix = dirname(dirname(titan_pkg_share))

    # /home/.../install/titan_nav/share
    titan_share_root = join(titan_prefix, "share")

    gz_sim_share = get_package_share_directory("ros_gz_sim")
    world_file = LaunchConfiguration("world_file")
    rviz_config = join(titan_pkg_share, "rviz", "titan.rviz")


    # export IGN_GAZEBO_RESOURCE_PATH=$IGN_GAZEBO_RESOURCE_PATH:$(ros2 pkg prefix titan_nav)/share
    # export IGN_GAZEBO_RESOURCE_PATH=$IGN_GAZEBO_RESOURCE_PATH:$(ros2 pkg prefix titan_nav)/share/titan_nav/models
    set_ign_resource_path = SetEnvironmentVariable(
        name="IGN_GAZEBO_RESOURCE_PATH",
        value=[
            EnvironmentVariable("IGN_GAZEBO_RESOURCE_PATH", default_value=""),
            ":",
            titan_share_root,
            ":",
            join(titan_pkg_share, "models")
        ]
    )

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
            join(titan_pkg_share, "launch", "rsp.launch.py")
        )
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": True}]
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "world_file",
            default_value=join(titan_pkg_share, "worlds", "small_warehouse.world"),
            description="Ignition Gazebo world file"
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true"
        ),

        set_ign_resource_path,

        gz_sim,
        spawn_titan_bot_node,
        rviz_node
    ])
