#!/usr/bin/python3

import os
from os.path import join
from xacro import parse, process_doc

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

from launch.actions import SetEnvironmentVariable

from launch_ros.parameter_descriptions import ParameterValue

titan_desc_share = get_package_share_directory("titan_description")

set_gazebo_path = SetEnvironmentVariable(
    name="IGN_GAZEBO_RESOURCE_PATH",
    value="home/titan/titan_ws/install"
)

def get_xacro_to_doc(xacro_file_path, mappings):
    doc = parse(open(xacro_file_path))
    process_doc(doc, mappings=mappings)
    return doc

def generate_launch_description():
   
    pixel_desc = get_package_share_directory("titan_description")
    pixel_bot_path = get_package_share_directory("pixel_simulation")
    position_x = LaunchConfiguration("position_x")
    position_y = LaunchConfiguration("position_y")
    orientation_yaw = LaunchConfiguration("orientation_yaw")

    robot_description = ParameterValue(
    Command([
    'xacro ',
    join(pixel_desc, 'urdf', 'titan_sim.urdf'),
    ' sim_ign:=true'
    ]),
    value_type=str
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[{
            'robot_description': robot_description
        }]
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "/robot_description",
            "-name", "pixel_simulation",
            "-allow_renaming", "true",
            "-z", "0.28",
            "-x", position_x,
            "-y", position_y,
            "-Y", orientation_yaw
        ]
    )
    
    gz_ros2_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/cmd_vel@geometry_msgs/msg/Twist@ignition.msgs.Twist",
            "/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock",
            "/odom@nav_msgs/msg/Odometry[ignition.msgs.Odometry",
            "/tf@tf2_msgs/msg/TFMessage[ignition.msgs.Pose_V",
            "/world/default/model/pixel_simulation/link/base_footprint/sensor/lidar/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan",
            "/world/default/model/pixel_simulation/joint_state@sensor_msgs/msg/JointState[ignition.msgs.Model",
            "/kinect_camera@sensor_msgs/msg/Image[ignition.msgs.Image",
            "/kinect_camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
            "/kinect_camera/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked",
            # "/stereo_camera/left/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image",
            "/camera/color/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image",
            # "/stereo_camera/left/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
            "/camera/color/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
        ],
        remappings=[
            ('/world/default/model/pixel_simulation/joint_state', '/joint_states'),
            ('/world/default/model/pixel_simulation/link/base_footprint/sensor/lidar/scan', '/scan'),
        ]
    )
    rviz_node = Node(
    package="rviz2",
    executable="rviz2",
    parameters=[{"use_sim_time": True}],
    arguments=["-d", join(pixel_bot_path, "config", "nav2_camera_view.rviz")],
)
   


    return LaunchDescription([
        rviz_node,
        DeclareLaunchArgument("position_x", default_value="0.0"),
        DeclareLaunchArgument("position_y", default_value="0.0"),
        DeclareLaunchArgument("orientation_yaw", default_value="0.0"),
        DeclareLaunchArgument("odometry_source", default_value="world"),
        robot_state_publisher,
        gz_spawn_entity, 
        gz_ros2_bridge ])