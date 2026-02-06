# ROS 2 Polygon Management System (Recording, Query, Execution Support)

This document describes the full developer-facing architecture and reference implementation for managing named polygons in ROS 2. The system supports:

1. Recording polygons interactively from RViz
2. Querying stored polygons
3. Providing polygon data to an existing execution engine

The design separates responsibilities across nodes and uses a dedicated interface package.

------------------------------------------------------------
SYSTEM OBJECTIVES
------------------------------------------------------------

OBJECTIVE 1 — Record Polygons Interactively  
Interface: ROS 2 Action  
Node: polygon_recorder_server

OBJECTIVE 2 — Query Stored Polygons  
Interface: ROS 2 Services  
Node: polygon_manager_node

OBJECTIVE 3 — Provide Polygon to Execution Engine  
Interface: ROS 2 Service (data provider only)  
Node: polygon_manager_node

------------------------------------------------------------
SHARED STORAGE FORMAT
------------------------------------------------------------

Polygons are stored in:
~/polygons.yaml

Example:

polygons:
  loading_zone:
    - [1.0, 2.0, 0.0]
    - [2.5, 3.1, 0.0]
    - [3.0, 1.2, 0.0]

------------------------------------------------------------
INTERFACE PACKAGE (RECOMMENDED NAME: polygon_interfaces)
------------------------------------------------------------

polygon_interfaces/
 ├── action/
 │   └── RecordPolygon.action
 └── srv/
     ├── ListPolygons.srv
     └── GetPolygon.srv

RecordPolygon.action

# Goal
string polygon_name
---
# Result
bool success
string message
geometry_msgs/Point[] polygon_points
---
# Feedback
int32 points_recorded

ListPolygons.srv

---
string[] polygon_names

GetPolygon.srv

string polygon_name
---
bool found
geometry_msgs/Point[] polygon

------------------------------------------------------------
NODE 1 — polygon_recorder_server (ACTION SERVER)
------------------------------------------------------------

Purpose: Records clicked points and writes polygons to YAML.

File: polygon_recorder_server.py

```python
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from geometry_msgs.msg import PointStamped, Point
from polygon_interfaces.action import RecordPolygon
import yaml
import os

class PolygonRecorderServer(Node):

    def __init__(self):
        super().__init__('polygon_recorder_server')

        self.declare_parameter('yaml_path', os.path.expanduser('~/polygons.yaml'))
        self.yaml_path = self.get_parameter('yaml_path').value

        self._action_server = ActionServer(
            self,
            RecordPolygon,
            'record_polygon',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback)

        self.subscription = self.create_subscription(
            PointStamped,
            '/clicked_point',
            self.point_callback,
            10)

        self.recording_active = False
        self.points = []

    def goal_callback(self, goal_request):
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        self.recording_active = True
        self.points = []
        name = goal_handle.request.polygon_name
        feedback = RecordPolygon.Feedback()

        while rclpy.ok() and goal_handle.is_active:
            feedback.points_recorded = len(self.points)
            goal_handle.publish_feedback(feedback)
            await rclpy.sleep(0.2)

        self.recording_active = False
        result = RecordPolygon.Result()
        result.polygon_points = self.points

        if len(self.points) < 3:
            result.success = False
            result.message = 'Polygon requires at least 3 points'
            goal_handle.abort()
            return result

        self.save_polygon(name, self.points)

        result.success = True
        result.message = 'Polygon saved'
        goal_handle.succeed()
        return result

    def point_callback(self, msg):
        if self.recording_active:
            p = Point(x=msg.point.x, y=msg.point.y, z=msg.point.z)
            self.points.append(p)

    def save_polygon(self, name, points):
        data = {}
        if os.path.exists(self.yaml_path):
            with open(self.yaml_path, 'r') as f:
                data = yaml.safe_load(f) or {}

        data.setdefault('polygons', {})
        data['polygons'][name] = [[p.x, p.y, p.z] for p in points]

        with open(self.yaml_path, 'w') as f:
            yaml.dump(data, f)


def main(args=None):
    rclpy.init(args=args)
    node = PolygonRecorderServer()
    rclpy.spin(node)
    rclpy.shutdown()
```

------------------------------------------------------------
NODE 2 — polygon_manager_node (SERVICE PROVIDER)
------------------------------------------------------------

Purpose: Loads YAML, serves polygon queries.

File: polygon_manager_node.py

```python
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point
from polygon_interfaces.srv import ListPolygons, GetPolygon
import yaml
import os

class PolygonManagerNode(Node):

    def __init__(self):
        super().__init__('polygon_manager_node')

        self.declare_parameter('yaml_path', os.path.expanduser('~/polygons.yaml'))
        self.yaml_path = self.get_parameter('yaml_path').value

        self.polygons = {}
        self.load_polygons()

        self.create_service(ListPolygons, 'polygon_manager/list_polygons', self.list_cb)
        self.create_service(GetPolygon, 'polygon_manager/get_polygon', self.get_cb)

    def load_polygons(self):
        if not os.path.exists(self.yaml_path):
            self.polygons = {}
            return

        with open(self.yaml_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        self.polygons = {}
        for name, pts in data.get('polygons', {}).items():
            self.polygons[name] = [Point(x=p[0], y=p[1], z=p[2]) for p in pts]

    def list_cb(self, request, response):
        response.polygon_names = list(self.polygons.keys())
        return response

    def get_cb(self, request, response):
        if request.polygon_name not in self.polygons:
            response.found = False
            return response

        response.found = True
        response.polygon = self.polygons[request.polygon_name]
        return response


def main(args=None):
    rclpy.init(args=args)
    node = PolygonManagerNode()
    rclpy.spin(node)
    rclpy.shutdown()
```

------------------------------------------------------------
LAUNCH FILE
------------------------------------------------------------

File: polygon_system.launch.py

```python
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument


def generate_launch_description():
    yaml_path = LaunchConfiguration('yaml_path')

    return LaunchDescription([
        DeclareLaunchArgument(
            'yaml_path',
            default_value='/home/user/polygons.yaml'
        ),

        Node(
            package='your_pkg',
            executable='polygon_recorder_server',
            name='polygon_recorder_server',
            parameters=[{'yaml_path': yaml_path}]
        ),

        Node(
            package='your_pkg',
            executable='polygon_manager_node',
            name='polygon_manager_node',
            parameters=[{'yaml_path': yaml_path}]
        )
    ])
```

Run system:
ros2 launch your_pkg polygon_system.launch.py yaml_path:=/home/user/polygons.yaml

------------------------------------------------------------
DEVELOPER NOTES
------------------------------------------------------------

Do not reload YAML on every service request. Load once and keep in memory.

Keep recording and querying in separate nodes.

Ensure RViz publishes `/clicked_point` in the correct frame.

Use parameters for file paths to avoid hardcoding.

Execution engine should call `/polygon_manager/get_polygon` before running its task.

------------------------------------------------------------
FINAL ARCHITECTURE SUMMARY
------------------------------------------------------------

Recording → Action Server  
Querying → Services  
Execution Input → Service data provider

This structure keeps the system modular, testable, and scalable.

