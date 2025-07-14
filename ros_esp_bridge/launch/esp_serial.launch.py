from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='ros_esp_bridge',
            executable='esp32_serial.py',
            name='esp32_serial_pub_sub',
            output='screen'
        )
    ])
