from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription
from launch_ros.substitutions import FindPackageShare
import os


def generate_launch_description():

    # -------------------------------
    # Launch arguments
    # -------------------------------
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    pkg_share = FindPackageShare('titan_nav').find('titan_nav')


    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock'
    )

    declare_map = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(
            pkg_share,
            'maps',
            'warehouse_map.yaml'
        ),
        description='Full path to map yaml file'
    )

    declare_params = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            pkg_share,
            'config',
            'nav2_param.yaml'
        ),
        description='Full path to Nav2 parameters file'
    )
    # -------------------------------
    # FORCE DEBUG LOGGING (planner timing)
    # -------------------------------
    set_debug_logging = SetEnvironmentVariable(
        name='RCUTILS_LOGGING_SEVERITY_THRESHOLD',
        value='DEBUG'
    )

    # -------------------------------
    # Nav2 Bringup (AMCL + Map + Nav)
    # -------------------------------
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                FindPackageShare('nav2_bringup').find('nav2_bringup'),
                'launch',
                'bringup_launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map': map_yaml,
            'params_file': params_file
        }.items()
    )

    # -------------------------------
    # Launch description
    # -------------------------------
    return LaunchDescription([
        declare_use_sim_time,
        declare_map,
        declare_params,
        set_debug_logging,   # <-- THIS IS THE ONLY ADDITION
        nav2_bringup
    ])
