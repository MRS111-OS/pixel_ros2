#!/usr/bin/python3

from os.path import join
from xacro import parse, process_doc

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command

from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory

def get_xacro_to_doc(xacro_file_path, mappings):
    doc = parse(open(xacro_file_path))
    process_doc(doc, mappings=mappings)
    return doc

def generate_launch_description():
   
    titan_bot_path = get_package_share_directory("titan_nav")
    position_x = LaunchConfiguration("position_x")
    position_y = LaunchConfiguration("position_y")
    orientation_yaw = LaunchConfiguration("orientation_yaw")

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[
                    {'robot_description': Command( \
                    ['xacro ', join(titan_bot_path, 'urdf/titan.urdf'),
                    ' sim_ign:=', "true"
                    ])}],
    )

    gz_spawn_entity = Node(
        package="ros_gz_sim",
        executable="create",
        arguments=[
            "-topic", "/robot_description",
            "-name", "titan_nav",
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
            "/world/default/model/titan_nav/link/base_footprint/sensor/lidar/scan@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan",
            "/world/default/model/titan_nav/joint_state@sensor_msgs/msg/JointState[ignition.msgs.Model",
            "/kinect_camera@sensor_msgs/msg/Image[ignition.msgs.Image",
            "/kinect_camera/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
            "/kinect_camera/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked",
            "/stereo_camera/left/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image",
            "/stereo_camera/right/image_raw@sensor_msgs/msg/Image[ignition.msgs.Image",
            "/stereo_camera/left/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
            "/stereo_camera/right/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo",
        ],
        remappings=[
            ('/world/default/model/titan_nav/joint_state', '/joint_states'),
            ('/world/default/model/titan_nav/link/base_footprint/sensor/lidar/scan', '/scan'),
        ]
    )

    rviz_node = Node(
    package='rviz2',
    executable='rviz2',
    arguments=['-d', join(titan_bot_path, 'config', 'titan3.rviz')]
)


    return LaunchDescription([
        DeclareLaunchArgument("position_x", default_value="0.0"),
        DeclareLaunchArgument("position_y", default_value="0.0"),
        DeclareLaunchArgument("orientation_yaw", default_value="0.0"),
        DeclareLaunchArgument("odometry_source", default_value="world"),
        robot_state_publisher,
        gz_spawn_entity, 
        gz_ros2_bridge ])