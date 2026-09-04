from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command, PathJoinSubstitution, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
import os
from launch.actions import TimerAction, DeclareLaunchArgument, SetEnvironmentVariable, IncludeLaunchDescription, ExecuteProcess
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    # Launch configurations
    map_yaml = LaunchConfiguration('map')
    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')

    # --- Declare launch arguments ---
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value='/home/gagasaga/titan_ws/src/titan_nav/maps/warehouse_map.yaml',
        description='Full path to map yaml file'
    )

    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock'
    )

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value='/home/gagasaga/titan_ws/src/titan_nav/config/nav2_param.yaml',
        description='full path to param file'
    )

    # --- Map server ---
    map_server_node = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{
            'yaml_filename': map_yaml,
            'use_sim_time': use_sim_time
        }]
    )

    bringup_map_server = TimerAction(
        period=2.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'run', 'nav2_util', 'lifecycle_bringup', 'map_server'],
            output='screen'
        )]
    )

    # --- AMCL ---
    amcl_node = Node(
        package='nav2_amcl',
        executable='amcl',
        name='amcl',
        output='screen',
        # remappings=[('/scan', '/scan')],
        parameters=[{
            'use_sim_time': use_sim_time,
            'use_map_topic': True,
            'min_particles': 500,
            'max_particles': 2000}]
    )

    bringup_amcl = TimerAction(
        period=4.0,
        actions=[ExecuteProcess(
            cmd=['ros2', 'run', 'nav2_util', 'lifecycle_bringup', 'amcl'],
            output='screen'
        )]
    )

    # --- Publish initial pose after AMCL is up ---
    initial_pose_node = Node(
        package='titan_nav',
        executable='publish_initial_pose',  # your C++ node
        name='initial_pose_publisher',
        output='screen'
    )

    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                FindPackageShare('nav2_bringup').find('nav2_bringup'),
                'launch',
                'navigation_launch.py'
            )
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map': map_yaml,
            'params_file': params_file
        }.items()
    )

    delayed_initial_pose = TimerAction(
        period=6.0,  # wait a few seconds to ensure AMCL is fully running
        actions=[initial_pose_node]
    )

    route_launch = Node(
    package='nav2_route',
    executable='route_server',
    name='route_server'
)


    return LaunchDescription([
        declare_map_yaml_cmd,
        declare_use_sim_time_cmd,
        declare_params_file_cmd,
        map_server_node,
        bringup_map_server,
        amcl_node,
        bringup_amcl,
        nav2_bringup,
        route_launch
        # delayed_initial_pose,  # <--- HERE
    ])