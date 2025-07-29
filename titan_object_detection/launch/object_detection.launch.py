from launch import LaunchDescription
from launch.actions import ExecuteProcess
import os

def generate_launch_description():
    pkg_src = os.path.join(os.getenv('HOME'), 'titan_ws', 'src', 'titan_object_detection', 'src')

    prototxt_path = os.path.join(pkg_src, 'MobileNetSSD_deploy.prototxt.txt')
    model_path = os.path.join(pkg_src, 'MobileNetSSD_deploy.caffemodel')
    script_path = os.path.join(pkg_src, 'real_time_object_detection.py')

    return LaunchDescription([
        ExecuteProcess(
            cmd=[
                'python3',
                script_path,
                '--prototxt', prototxt_path,
                '--model', model_path,
                '--confidence', '0.3'
            ],
            output='screen'
        )
    ])
