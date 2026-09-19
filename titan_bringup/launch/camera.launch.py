#!/usr/bin/env python3

from ament_index_python.resources import has_resource

from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.launch_description import LaunchDescription
from launch.substitutions import LaunchConfiguration

from launch_ros.actions import ComposableNodeContainer, Node
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

    # Lower defaults to 320x240 for low-latency WiFi streaming.
    # Override at launch: ros2 launch titan_bringup camera.launch.py width:=640 height:=480
    width_name = 'width'
    width_default = '320'

    width_param = LaunchConfiguration(width_name)

    width_launch_arg = DeclareLaunchArgument(
        width_name,
        default_value=width_default,
        description='Image width (lower = less lag over WiFi)'
    )

    height_name = 'height'
    height_default = '240'

    height_param = LaunchConfiguration(height_name)

    height_launch_arg = DeclareLaunchArgument(
        height_name,
        default_value=height_default,
        description='Image height (lower = less lag over WiFi)'
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
    # NOTE: Camera inversion (180°) is handled at hardware level via:
    #   /boot/firmware/config.txt -> dtoverlay=ov5647,vflip=1,hflip=1
    # The 'orientation' param in camera_ros requires libcamera >= 0.2.0
    # which is NOT shipped on Raspberry Pi OS Humble by default.

    composable_nodes = [

        # CAMERA NODE
        ComposableNode(
            package='camera_ros',
            plugin='camera::CameraNode',
            name='camera',
            parameters=[{

                # Camera selection
                'camera': camera_param,

                # Resolution (keep low for WiFi streaming)
                'width': width_param,
                'height': height_param,

                # Valid ROS-compatible format
                'format': format_param,

                # Use URDF optical frame
                'frame_id': 'RGB_Camera_Optical_Link',

                # Drop old frames — keep only the latest to minimise latency
                'buffer_queue_size': 1,

                # Use node clock to avoid timestamp drift causing viewer lag
                'use_node_time': True,

            }],
            extra_arguments=[{
                # Zero-copy intra-process: images never leave the container
                'use_intra_process_comms': True
            }],
            # Remap raw output → unflipped topic so flip_image.py can process it
            # Match private (~/image_raw), absolute (/camera/image_raw), and relative (image_raw)
            remappings=[
                ('~/image_raw',        '/camera/image_raw_unflipped'),
                ('/camera/image_raw',  '/camera/image_raw_unflipped'),
                ('image_raw',          '/camera/image_raw_unflipped'),
            ],
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

    # ================= SOFTWARE 180° IMAGE FLIP & COMPRESSION =================
    # Subscribes to the raw unflipped topic, rotates 180° using OpenCV, and
    # publishes a standard flipped raw topic plus an on-demand JPEG stream.
    flip_node = Node(
        package='titan_bringup',
        executable='flip_image.py',
        name='flip_image',
        remappings=[
            ('image_in',             '/camera/image_raw_unflipped'),
            ('image_out',            '/camera/image_raw'),
            ('image_out/compressed', '/camera/image_raw/compressed'),
        ],
        output='screen',
    )

    return LaunchDescription([

        camera_launch_arg,
        format_launch_arg,

        width_launch_arg,
        height_launch_arg,

        use_image_view_launch_arg,

        container,
        flip_node,
    ])
