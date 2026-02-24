import os
import launch
import launch_ros
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.substitutions import FindPackageShare
from launch.actions import IncludeLaunchDescription, ExecuteProcess, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

package_name = 'titan_bringup'
desc_pkg = 'titan_description'

def generate_launch_description():
    pkg_share = FindPackageShare(package=package_name).find(package_name)
    desc_share = FindPackageShare(package=desc_pkg).find(desc_pkg)

    rviz_launch_path = os.path.join(pkg_share, 'launch', 'rviz2.launch.py')
    state_launch_path = os.path.join(pkg_share, 'launch', 'titan_state_publisher.launch.py')

    # URDF/Xacro path
    urdf_file = os.path.join(desc_share, 'urdf', 'turtlebot3_burger.urdf')

    # Load URDF content
    with open(urdf_file, 'r') as file:
        robot_description_content = file.read()

    robot_description_param = {'robot_description': robot_description_content}


    # GUI for joint states
    joint_state_publisher_gui_node = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        output='screen'
    )

    rviz_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rviz_launch_path)
    )

    turtlebot_state_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(state_launch_path)
    )

    return launch.LaunchDescription([
        joint_state_publisher_gui_node,
        rviz_launch,
        turtlebot_state_launch,
    ])
