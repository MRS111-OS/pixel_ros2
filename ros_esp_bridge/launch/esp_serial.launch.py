from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='esp32_serial_bridge',
            executable='serial_pub_sub_node',
            name='esp32_serial_pub_sub',
            output='screen'
        )
    ])
