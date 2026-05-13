#!/usr/bin/env python3

from ament_index_python.resources import has_resource

from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.launch_description import LaunchDescription
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description() -> LaunchDescription:

    # ================= CAMERA DEVICE =================

    camera_param_name = 'camera'
    camera_param_default = '0'

    camera_param = LaunchConfiguration(
        camera_param_name,
        default=camera_param_default,
    )

    camera_launch_arg = DeclareLaunchArgument(
        camera_param_name,
        default_value=camera_param_default,
        description='camera ID or name'
    )

    # ================= IMAGE FORMAT =================

    format_param_name = 'format'
    format_param_default = 'RGB888'

    format_param = LaunchConfiguration(
        format_param_name,
        default=format_param_default,
    )

    format_launch_arg = DeclareLaunchArgument(
        format_param_name,
        default_value=format_param_default,
        description='Camera pixel format'
    )

    # ================= RESOLUTION =================

    width_name = 'width'
    width_default = '640'

    width_param = LaunchConfiguration(width_name)

    width_launch_arg = DeclareLaunchArgument(
        width_name,
        default_value=width_default,
        description='Image width'
    )

    height_name = 'height'
    height_default = '480'

    height_param = LaunchConfiguration(height_name)

    height_launch_arg = DeclareLaunchArgument(
        height_name,
        default_value=height_default,
        description='Image height'
    )

    # ================= IMAGE VIEW =================

    use_image_view_name = 'use_image_view'
    use_image_view_default = 'false'

    use_image_view_param = LaunchConfiguration(use_image_view_name)

    use_image_view_launch_arg = DeclareLaunchArgument(
        use_image_view_name,
        default_value=use_image_view_default,
        description='Launch image_view'
    )

    # ================= CAMERA NODE =================

    composable_nodes = [

        # CAMERA NODE
        ComposableNode(
            package='camera_ros',
            plugin='camera::CameraNode',
            name='camera',
            parameters=[{

                # Camera selection
                'camera': camera_param,

                # Resolution
                'width': width_param,
                'height': height_param,

                # Valid ROS-compatible format
                'format': format_param,

                # Use URDF optical frame
                'frame_id': 'RGB_Camera_Optical_Link',

                # Reduce latency
                'buffer_queue_size': 1,

            }],
            extra_arguments=[{
                'use_intra_process_comms': True
            }],
        ),

        # COMPRESSED IMAGE TRANSPORT
        ComposableNode(
            package='image_transport',
            plugin='image_transport::RepublishNode',
            name='image_compressor',
            remappings=[
                ('in', '/camera/image_raw'),
                ('out/compressed', '/camera/image_raw/compressed'),
            ],
            parameters=[{
                'in_transport': 'raw',
                'out_transport': 'compressed',
            }],
            extra_arguments=[{
                'use_intra_process_comms': True
            }],
        ),
    ]

    # ================= OPTIONAL IMAGE VIEW =================

    if has_resource('packages', 'image_view'):

        composable_nodes.append(

            ComposableNode(
                package='image_view',
                plugin='image_view::ImageViewNode',
                name='image_view',

                remappings=[
                    ('image', '/camera/image_raw')
                ],

                extra_arguments=[{
                    'use_intra_process_comms': True
                }],

                condition=IfCondition(use_image_view_param),
            )
        )

    # ================= CONTAINER =================

    container = ComposableNodeContainer(
        name='camera_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container_mt',
        composable_node_descriptions=composable_nodes,
        output='screen',
    )

    return LaunchDescription([

        camera_launch_arg,
        format_launch_arg,

        width_launch_arg,
        height_launch_arg,

        use_image_view_launch_arg,

        container,
    ])