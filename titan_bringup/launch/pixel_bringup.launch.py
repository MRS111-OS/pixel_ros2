import os
import launch
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare
from launch_ros.actions import Node


package_name = 'titan_bringup'
desc_pkg = 'titan_description'


def generate_launch_description():

    # -------------------------------------------------
    # Package paths
    # -------------------------------------------------
    pkg_share = FindPackageShare(package=package_name).find(package_name)
    lidar_share = FindPackageShare(package='sllidar_ros2').find('sllidar_ros2')
    lidar_filter_share = FindPackageShare(
        package='laser_filters').find('laser_filters')

    # -------------------------------------------------
    # Launch file paths
    # -------------------------------------------------
    state_launch_path = os.path.join(
        pkg_share,
        'launch',
        'titan_state_publisher.launch.py'
    )

    lidar_launch_path = os.path.join(
        lidar_share,
        'launch',
        'sllidar_c1_launch.py'
    )

    laser_filter_launch_path = os.path.join(
        lidar_filter_share,
        'examples',
        'box_filter_example.launch.py'
    )

    # -------------------------------------------------
    # micro-ROS Agent (NOW USING NODE)
    # -------------------------------------------------
    micro_ros_agent_node = Node(
        package='micro_ros_agent',
        executable='micro_ros_agent',
        name='micro_ros_agent',
        output='screen',
        arguments=[
            'serial',
            '--dev', '/dev/ttyACM0',
            '-b', '115200'
        ]
    )

    # -------------------------------------------------
    # Included launches
    # -------------------------------------------------
    turtlebot_state_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(state_launch_path)
    )

    lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lidar_launch_path)
    )

    laser_filter_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(laser_filter_launch_path)
    )

    # -------------------------------------------------
    # Final Launch Description
    # -------------------------------------------------
    return launch.LaunchDescription([

        # Start micro-ROS agent
        micro_ros_agent_node,

        # Robot state publisher
        turtlebot_state_launch,

        # Delay lidar startup
        TimerAction(
            period=5.0,
            actions=[lidar_launch]
        ),

        # Delay laser filter startup
        TimerAction(
            period=8.0,
            actions=[laser_filter_launch]
        ),
    ])
