import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # ---- YOUR FILES ----
    map_yaml_file = '/home/gagasaga/titan_ws/src/titan_nav/maps/warehouse_map.yaml'
    graph_filepath = '/home/gagasaga/titan_ws/src/titan_nav/config/warehouse_map.json'
    params_file = '/home/gagasaga/titan_ws/src/titan_nav/config/nav2_param.yaml'

    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Ignition simulation clock'
    )

    # ---- Nav2 + Route Server ----
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')
        ),
        launch_arguments={
            'map': map_yaml_file,
            'graph': graph_filepath,
            'params_file': params_file,
            'use_sim_time': use_sim_time
        }.items()
    )

    return LaunchDescription([
        declare_use_sim_time,
        nav2_bringup
    ])
