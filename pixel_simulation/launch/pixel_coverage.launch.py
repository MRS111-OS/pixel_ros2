# Copyright (c) 2023 Open Navigation LLC
# Licensed under the Apache License, Version 2.0

import os

from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable, DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import LoadComposableNodes, Node
from launch_ros.descriptions import ComposableNode, ParameterFile

from ament_index_python.packages import get_package_share_directory
from nav2_common.launch import RewrittenYaml


package_name = 'pixel_simulation'


def generate_launch_description():

    # -------------------------
    # Launch Configurations
    # -------------------------
    use_sim_time = LaunchConfiguration('use_sim_time')
    autostart = LaunchConfiguration('autostart')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true')

    declare_autostart = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Automatically startup the nav2 stack')

    # -------------------------
    # Paths
    # -------------------------
    params_file = os.path.join(
        get_package_share_directory(package_name),
        'config',
        'coverage.yaml'
    )

    map_file = os.path.join(
        get_package_share_directory(package_name),
        'maps',
        'warehouse_map.yaml'
    )

    # -------------------------
    # Lifecycle Nodes
    # -------------------------
    lifecycle_nodes = [
            'amcl',
            'map_server',
            'controller_server',
            'planner_server',
            'bt_navigator',
            'velocity_smoother',
            'coverage_server'
    ]

    # -------------------------
    # Remappings
    # -------------------------
    remappings = [
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static')
    ]

    # -------------------------
    # Parameter Substitutions
    # -------------------------
    param_substitutions = {
        'use_sim_time': use_sim_time,
        'autostart': autostart
    }

    configured_params = ParameterFile(
        RewrittenYaml(
            source_file=params_file,
            root_key='',
            param_rewrites=param_substitutions,
            convert_types=True
        ),
        allow_substs=True
    )

    # -------------------------
    # Environment Variable
    # -------------------------
    stdout_linebuf_envvar = SetEnvironmentVariable(
        'RCUTILS_LOGGING_BUFFERED_STREAM',
        '1'
    )

    # -------------------------
    # Component Container
    # -------------------------
    create_container = Node(
        name='nav2_container',
        package='rclcpp_components',
        executable='component_container_isolated',
        parameters=[configured_params],
        remappings=remappings,
        output='screen'
    )

    # -------------------------
    # Load Composable Nodes
    # -------------------------
    load_composable_nodes = LoadComposableNodes(
        target_container='nav2_container',
        composable_node_descriptions=[

            # -------------------------
            # Planner Server (GLOBAL COSTMAP)
            # -------------------------
            ComposableNode(
                package='nav2_planner',
                plugin='nav2_planner::PlannerServer',
                name='planner_server',
                parameters=[configured_params],
                remappings=remappings
            ),

            # -------------------------
            # Controller Server (LOCAL COSTMAP)
            # -------------------------
            ComposableNode(
                package='nav2_controller',
                plugin='nav2_controller::ControllerServer',
                name='controller_server',
                parameters=[configured_params],
                remappings=remappings + [('cmd_vel', 'cmd_vel_nav')]
            ),

            # -------------------------
            # Coverage Server
            # -------------------------
            ComposableNode(
                package='opennav_coverage',
                plugin='opennav_coverage::CoverageServer',
                name='coverage_server',
                parameters=[configured_params],
                remappings=remappings
            ),

            # -------------------------
            # BT Navigator
            # -------------------------
            ComposableNode(
                package='backported_bt_navigator',
                plugin='backported_bt_navigator::BtNavigator',
                name='bt_navigator',
                parameters=[configured_params],
                remappings=remappings
            ),

            # -------------------------
            # Velocity Smoother
            # -------------------------
            ComposableNode(
                package='nav2_velocity_smoother',
                plugin='nav2_velocity_smoother::VelocitySmoother',
                name='velocity_smoother',
                parameters=[configured_params],
                remappings=remappings +
                           [('cmd_vel', 'cmd_vel_nav'),
                            ('cmd_vel_smoothed', 'cmd_vel')]
            ),

            # -------------------------
            # Map Server
            # -------------------------
            ComposableNode(
                package='nav2_map_server',
                plugin='nav2_map_server::MapServer',
                name='map_server',
                parameters=[configured_params,
                            {'yaml_filename': map_file}],
                remappings=remappings
            ),

            # -------------------------
            # AMCL
            # -------------------------
            ComposableNode(
                package='nav2_amcl',
                plugin='nav2_amcl::AmclNode',
                name='amcl',
                parameters=[configured_params],
                remappings=remappings
            ),

            # -------------------------
            # Lifecycle Manager
            # -------------------------
            ComposableNode(
                package='nav2_lifecycle_manager',
                plugin='nav2_lifecycle_manager::LifecycleManager',
                name='lifecycle_manager_navigation',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'autostart': autostart,
                    'node_names': lifecycle_nodes
                }]
            ),
        ],
    )

    # -------------------------
    # Launch Description
    # -------------------------
    ld = LaunchDescription()

    ld.add_action(declare_use_sim_time)
    ld.add_action(declare_autostart)
    ld.add_action(stdout_linebuf_envvar)
    ld.add_action(create_container)
    ld.add_action(load_composable_nodes)

    return ld