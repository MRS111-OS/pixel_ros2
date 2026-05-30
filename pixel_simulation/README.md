# Pixel Simulation - Coverage Planning System

Complete ROS2 Humble coverage planning and navigation system for the Pixel robot with simulation in Gazebo.

---

## Table of Contents

1. [File Structure](#file-structure)
2. [Nodes](#nodes)
3. [Launch Files](#launch-files)
4. [Services](#services)
5. [Actions](#actions)
6. [Step-by-Step Coverage Execution](#step-by-step-coverage-execution)
7. [Examples](#examples)

---

## File Structure

```
pixel_simulation/
├── README.md                          # This file
├── CMakeLists.txt                     # Build configuration
├── package.xml                        # Package manifest
│
├── src/                               # Python/C++ source files
│   ├── execute_polygon.py             # Execute pre-recorded polygon coverage
│   ├── execute_polygon                # Executable (no .py extension)
│   ├── polygon_manager_node.py        # Polygon storage/retrieval manager
│   ├── polygon_recorder_server.py     # Record polygons from RViz clicks
│   ├── points.py                      # Reference: Interactive polygon from RViz clicks
│   ├── joy_node.cpp                   # Joystick control interface
│   ├── publish_initial_pose.cpp       # Initial pose publisher
│   └── points_backup.py               # Backup reference implementation
│
├── launch/                            # Launch files
│   ├── bringup_sim.launch.py          # Gazebo simulator + robot spawning
│   ├── pixel_coverage.launch.py       # Nav2 coverage planning stack
│   ├── polygon_system.launch.py       # Polygon manager + recorder
│   ├── pixel_nav.launch.py            # Basic navigation stack
│   ├── rsp.launch.py                  # Robot state publisher (URDF/XACRO)
│   └── slam.launch.py                 # SLAM mapping
│
├── config/                            # Configuration files
│   ├── polygon.yaml                   # Pre-recorded polygon definitions
│   ├── coverage.yaml                  # Nav2 coverage planning parameters
│   ├── bringup_sim.rviz               # RViz configuration
│   ├── sim.rviz                       # Alternative RViz config
│   ├── clicked_complete_coverage.xml  # Behavior tree (coverage with RViz clicks)
│   └── simple_nav_to_pose.xml         # Behavior tree (simple navigation)
│
├── maps/                              # Map files
│   └── warehouse_map.yaml             # Warehouse environment map
│
├── models/                            # Robot models
│   └── (Gazebo robot models)
│
└── worlds/                            # Gazebo worlds
    └── (Gazebo world definitions)
```

---

## Nodes

### 1. **polygon_manager_node.py**
**Purpose**: Persistent polygon storage and retrieval manager

**Location**: `src/polygon_manager_node.py`

**Functionality**:
- Loads polygons from YAML file
- Provides two services for polygon access
- Thread-safe for concurrent requests

**Launched By**: `polygon_system.launch.py`

**Key Methods**:
- `load_polygons()` - Load from YAML on startup
- `list_polygons_callback()` - Return list of polygon names
- `get_polygon_callback()` - Return specific polygon points

---

### 2. **polygon_recorder_server.py**
**Purpose**: Record polygon vertices from RViz clicked points

**Location**: `src/polygon_recorder_server.py`

**Functionality**:
- Provides action server for recording polygons
- Listens to `/clicked_point` topic from RViz
- Auto-saves polygons to YAML
- Uses `MultiThreadedExecutor` for concurrent execution
  - Prevents subscriber callback starvation
  - Allows simultaneous action loop + point recording

**Launched By**: `polygon_system.launch.py`

**Threading Model**:
```
SingleThreadedExecutor (default) - BLOCKED
  Action loop blocks executor
  ↓ Subscriber never runs
  ↓ Points never recorded

MultiThreadedExecutor (our model) - CONCURRENT
  Action loop (Thread 1) + Subscriber (Thread 2+) run in parallel
  ↓ Points recorded while action runs
```

---

### 3. **execute_polygon.py**
**Purpose**: Execute coverage on a pre-recorded polygon by name

**Location**: `src/execute_polygon.py`

**Functionality**:
- Retrieves polygon from polygon_manager via GetPolygon service
- Generates coverage path via ComputeCoveragePath action
- Navigates to first point via NavigateToPose
- Executes full coverage path via FollowPath
- Single-shot execution (timer cancelled after start)

**Execution Pipeline**:
```
1. [STARTUP] Poll bt_navigator until active
2. [POLYGON] Retrieve polygon from YAML
3. [COVERAGE] Generate zig-zag coverage path
4. [NAVIGATE] Go to first coverage point
5. [FOLLOW_PATH] Execute full coverage path
6. [COMPLETE] Mission finished
```

**Run Command**:
```bash
ros2 run pixel_simulation execute_polygon --ros-args -p polygon_name:=Field_1
```

---

### 4. **points.py** (Reference Implementation)
**Purpose**: Interactive coverage execution from RViz clicked points

**Location**: `src/points.py`

**Functionality**:
- Click 4 points in RViz to define polygon
- Orders points and closes polygon
- Generates coverage path automatically
- Executes NavigateToPose + FollowPath pipeline

**Run Command**:
```bash
ros2 run pixel_simulation points.py
```

**Workflow**:
1. Run node and RViz
2. Click 4 points in 3D view
3. Coverage path generates automatically
4. Robot navigates and executes

---

## Launch Files

### 1. **bringup_sim.launch.py**
**Purpose**: Gazebo simulator + robot + navigation components

**What it does**:
- Launches Gazebo physics engine
- Spawns Pixel robot in warehouse
- Loads robot state publisher (URDF)
- Activates TF broadcasting

**Run Command**:
```bash
ros2 launch pixel_simulation bringup_sim.launch.py
```

**Arguments**:
```bash
ros2 launch pixel_simulation bringup_sim.launch.py world_file:=warehouse.world
```

---

### 2. **pixel_coverage.launch.py**
**Purpose**: Nav2 coverage planning and navigation stack

**What it does**:
- Starts AMCL localization
- Loads warehouse map
- Initializes coverage planner (opennav_coverage)
- Starts controller server
- Loads behavior tree navigator
- Activates all lifecycle nodes

**Run Command**:
```bash
ros2 launch pixel_simulation pixel_coverage.launch.py use_sim_time:=true
```

**Arguments**:
```bash
use_sim_time    : Use Gazebo clock if true (default: true)
autostart       : Auto-startup nav2 stack (default: true)
```

---

### 3. **polygon_system.launch.py**
**Purpose**: Polygon management system

**What it does**:
- Launches polygon_manager_node
- Launches polygon_recorder_server
- Shares YAML polygon file between nodes

**Run Command**:
```bash
ros2 launch pixel_simulation polygon_system.launch.py
```

**Arguments** (optional, uses default if omitted):
```bash
# Use custom polygon file (default: <package>/config/polygon.yaml)
ros2 launch pixel_simulation polygon_system.launch.py \
  yaml_path:=/path/to/custom/polygon.yaml
```

---

## Services

### 1. `/polygon_manager/list_polygons` (ListPolygons)

**Purpose**: Get list of available polygon names

**Service Definition**:
```
Request:  (empty)
Response: polygon_names: string[]
```

**Example**:
```bash
ros2 service call /polygon_manager/list_polygons polygon_interfaces/srv/ListPolygons
```

**Expected Output**:
```
requester: making request: ListPolygons_Request()

response: polygon_names: ['Field_1', 'Field_2', 'Field_3']
```

---

### 2. `/polygon_manager/get_polygon` (GetPolygon)

**Purpose**: Retrieve polygon points by name

**Service Definition**:
```
Request:  polygon_name: string
Response: found: bool
          polygon: geometry_msgs/Point[]
```

**Example**:
```bash
ros2 service call /polygon_manager/get_polygon \
  polygon_interfaces/srv/GetPolygon \
  "{polygon_name: 'Field_1'}"
```

**Expected Output**:
```
response: found: true
          polygon:
          - {x: 0.99, y: -3.44, z: 0.0}
          - {x: -2.41, y: -3.54, z: 0.0}
          - {x: -2.31, y: -0.65, z: 0.0}
          - {x: 0.6, y: -1.07, z: 0.0}
```

---

### 3. `/bt_navigator/get_state` (GetState)

**Purpose**: Query behavior tree navigator lifecycle state

**Service Definition**:
```
Request:  (empty)
Response: current_state: lifecycle_msgs/State
          transition_graph: string[]
```

**Example**:
```bash
ros2 service call /bt_navigator/get_state lifecycle_msgs/srv/GetState
```

**Expected Output**:
```
response: current_state: {id: 3, label: 'active'}
```

**States**:
- `1`: unknown
- `2`: unconfigured
- `3`: inactive (configured but not active)
- `4`: active (ready to receive goals)

---

## Actions

### 1. `/compute_coverage_path` (ComputeCoveragePath)

**Purpose**: Generate zig-zag coverage path for polygon

**Action Definition**:
```
Goal:    frame_id: string
         polygons: Coordinates[]    # Polygon boundary
         generate_headland: bool     # Add buffer zone
         generate_route: bool        # Connect paths
         generate_path: bool         # Create waypoint path
         
Result:  nav_path: nav_msgs/Path    # Coverage waypoints
         planning_time: float64
         
Feedback: current_progress: uint32   # Percentage complete
```

**Example - Using ros2 CLI**:
```bash
# Start action
ros2 action send_goal /compute_coverage_path \
  opennav_coverage_msgs/action/ComputeCoveragePath \
  '{goal: {frame_id: "map", polygons: [{coordinates: [{axis1: 0.99, axis2: -3.44}, {axis1: -2.41, axis2: -3.54}, {axis1: -2.31, axis2: -0.65}, {axis1: 0.6, axis2: -1.07}, {axis1: 0.99, axis2: -3.44}]}], generate_route: true, generate_path: true, generate_headland: false}}'
```

**Example - From Code** (see execute_polygon.py):
```python
goal = ComputeCoveragePath.Goal()
goal.frame_id = 'map'
goal.polygons.append(coords)
goal.generate_headland = False
goal.generate_route = True
goal.generate_path = True

send_goal_future = self.compute_coverage_client.send_goal_async(goal)
send_goal_future.add_done_callback(self.compute_goal_response)
```

---

### 2. `/navigate_to_pose` (NavigateToPose)

**Purpose**: Navigate robot to goal pose

**Action Definition**:
```
Goal:    pose: geometry_msgs/PoseStamped  # Goal position + orientation
         
Result:  (empty)
         
Feedback: current_pose: geometry_msgs/PoseStamped
          navigation_time: builtin_interfaces/Duration
          estimated_time_remaining: builtin_interfaces/Duration
          number_of_recoveries: uint32
          distance_remaining: float32
```

**Example - Using ros2 CLI**:
```bash
ros2 action send_goal /navigate_to_pose \
  nav2_msgs/action/NavigateToPose \
  '{pose: {header: {frame_id: "map"}, pose: {position: {x: 0.99, y: -3.44}, orientation: {w: 1.0}}}}'
```

**Example - From Code** (see execute_polygon.py):
```python
goal = NavigateToPose.Goal()
goal.pose = target_pose

send_goal_future = self.navigate_to_pose_client.send_goal_async(goal)
send_goal_future.add_done_callback(self.navigate_goal_response)
```

---

### 3. `/follow_path` (FollowPath)

**Purpose**: Execute pre-planned path with controller

**Action Definition**:
```
Goal:    path: nav_msgs/Path              # Waypoint sequence
         controller_id: string             # Controller type
         goal_checker_id: string           # Goal verification
         
Result:  (empty)
         
Feedback: current_pose: geometry_msgs/PoseStamped
          current_speed: geometry_msgs/Twist
          time_elapsed: builtin_interfaces/Duration
```

**Example - Using ros2 CLI**:
```bash
# This is complex and typically not called directly
# See execute_polygon.py for proper usage
```

**Example - From Code** (see execute_polygon.py):
```python
goal = FollowPath.Goal()
goal.path = self.coverage_nav_path
goal.controller_id = 'FollowPath'
goal.goal_checker_id = ''

send_goal_future = self.follow_path_client.send_goal_async(goal)
send_goal_future.add_done_callback(self.follow_goal_response)
```

---

## Step-by-Step Coverage Execution

Complete walkthrough of executing coverage on a pre-recorded polygon.

### Prerequisites

- ROS2 Humble installed
- Pixel simulation built: `colcon build --packages-select pixel_simulation`
- Polygon defined in `config/polygon.yaml`

### Execution Steps

#### **Step 1: Start Gazebo Simulator + Robot**

```bash
ros2 launch pixel_simulation bringup_sim.launch.py
```

**What happens**:
- Gazebo opens with warehouse world
- Pixel robot spawns at origin
- TF tree broadcasting starts

**Expected Output**:
```
[gzserver-1] [INFO] [rcl]: Found security directory: /root/.ros/security
[gzserver-1] Started Gazebo server
[gzclient-1] Started Gazebo client
```

**Verification** (new terminal):
```bash
ros2 topic list | grep /
```
Should show `/clock`, `/tf`, robot sensors, etc.

---

#### **Step 2: Launch Navigation + Coverage Stack**

```bash
ros2 launch pixel_simulation pixel_coverage.launch.py use_sim_time:=true
```

**What happens**:
- AMCL localization node starts
- Map server loads warehouse map
- Coverage planner initializes
- Behavior tree navigator activates
- All lifecycle nodes transition to **active**

**Expected Output**:
```
[map_server-2] [INFO] [map_server]: ...Creating BT Navigator...
[planner_server-3] [INFO] [planner_server]: Navigation2 Planner Server...
[controller_server-4] [INFO] [controller_server]: Navigation2 Controller Server...
[bt_navigator-5] [INFO] [bt_navigator]: ...BT Navigator ready...
```

**Verification** (new terminal):
```bash
ros2 service call /bt_navigator/get_state lifecycle_msgs/srv/GetState
# Should return: current_state: {id: 4, label: 'active'}
```

---

#### **Step 3: Launch Polygon Management System**

```bash
ros2 launch pixel_simulation polygon_system.launch.py
```

**What happens**:
- polygon_manager_node loads YAML file
- polygon_recorder_server starts (listens for RViz clicks)
- Both nodes share the polygon file

**Expected Output**:
```
[polygon_manager-6] [INFO] [polygon_manager_node]: PolygonManagerNode initialized...
[polygon_manager-6] [INFO] [polygon_manager_node]: Loaded 2 polygons: ['Field_1', 'Field_2']
[polygon_recorder-7] [INFO] [polygon_recorder_server]: PolygonRecorderServer initializing...
```

**Verification** (new terminal):
```bash
ros2 service call /polygon_manager/list_polygons \
  polygon_interfaces/srv/ListPolygons
# Should return list of available polygons
```

---

#### **Step 4: Execute Polygon Coverage**

```bash
ros2 run pixel_simulation execute_polygon --ros-args -p polygon_name:=Field_1
```

**What happens**:
- Node initializes and checks BT navigator state
- Requests Field_1 polygon from manager
- Generates coverage path (zig-zag)
- Navigates to first point
- Executes full coverage path
- Logs each stage with [COVERAGE], [NAVIGATE], [FOLLOW_PATH] tags

**Expected Output**:
```
[execute_polygon_node-8] [INFO] ExecutePolygonNode initialized for polygon: Field_1
[execute_polygon_node-8] [INFO] [STARTUP] Requesting bt_navigator state...
[execute_polygon_node-8] [INFO] [STARTUP] BT navigator state: active
[execute_polygon_node-8] [INFO] [STARTUP] ✓ BT navigator is active, requesting polygon...
[execute_polygon_node-8] [INFO] [STARTUP] *** MISSION START: Timer cancelled, beginning single-shot mission pipeline ***
[execute_polygon_node-8] [INFO] [POLYGON] Requesting polygon: Field_1
[execute_polygon_node-8] [INFO] [POLYGON] Polygon found
[execute_polygon_node-8] [INFO] [POLYGON] Number of points: 4
[execute_polygon_node-8] [INFO] [COVERAGE] >>> STEP 1/4: Sending ComputeCoveragePath action...
[execute_polygon_node-8] [INFO] [COVERAGE] Sending ComputeCoveragePath goal (only once)...
[execute_polygon_node-8] [INFO] [COVERAGE] Goal accepted, waiting for result...
[execute_polygon_node-8] [INFO] [COVERAGE] ✓ Coverage path computed with 169 poses
[execute_polygon_node-8] [INFO] [NAVIGATE] >>> STEP 2/4: Navigate to first coverage point...
[execute_polygon_node-8] [INFO] [NAVIGATE] Sending NavigateToPose goal to (-2.064, -3.533) (only once)...
[execute_polygon_node-8] [INFO] [NAVIGATE] Goal accepted, waiting for result...
[execute_polygon_node-8] [INFO] [NAVIGATE] Goal status: 4
[execute_polygon_node-8] [INFO] [NAVIGATE] ✓ Reached first point! Starting FollowPath...
[execute_polygon_node-8] [INFO] [FOLLOW_PATH] >>> STEP 3/4: Execute full coverage path...
[execute_polygon_node-8] [INFO] [FOLLOW_PATH] Sending FollowPath goal (only once)...
[execute_polygon_node-8] [INFO] [FOLLOW_PATH] Goal accepted, waiting for result...
[execute_polygon_node-8] [INFO] [FOLLOW_PATH] Goal status: 4
[execute_polygon_node-8] [INFO] [FOLLOW_PATH] >>> STEP 4/4: COMPLETE <<<
[execute_polygon_node-8] [INFO] [FOLLOW_PATH] *** MISSION FINISHED: Coverage path traversal complete! ***
```

**In RViz**:
- Robot moves to Field_1 location
- Follows zig-zag coverage path
- Completes coverage and returns

---

### Alternative: Interactive Coverage with RViz Clicks

If you prefer to click points in RViz instead:

```bash
ros2 run pixel_simulation points.py
```

**Workflow**:
1. Click 4 points in RViz 3D view
2. Robot generates coverage automatically
3. Executes navigation + path following

---

## Examples

### Example 1: Record a New Polygon

**Terminal 1** (Gazebo):
```bash
ros2 launch pixel_simulation bringup_sim.launch.py
```

**Terminal 2** (Navigation):
```bash
ros2 launch pixel_simulation pixel_coverage.launch.py use_sim_time:=true
```

**Terminal 3** (RViz + Polygon Recording):
```bash
ros2 launch pixel_simulation polygon_system.launch.py
# Then open RViz and use the publish point tool to record polygon
```

**Recorded polygons saved to**: `config/polygon.yaml`

---

### Example 2: Execute Multiple Polygons Sequentially

```bash
# Execute Field_1
ros2 run pixel_simulation execute_polygon --ros-args -p polygon_name:=Field_1

# Wait for completion...

# Execute Field_2
ros2 run pixel_simulation execute_polygon --ros-args -p polygon_name:=Field_2
```

---

### Example 3: Check Polygon Data

```bash
# List all polygons
ros2 service call /polygon_manager/list_polygons \
  polygon_interfaces/srv/ListPolygons

# Get specific polygon
ros2 service call /polygon_manager/get_polygon \
  polygon_interfaces/srv/GetPolygon \
  "{polygon_name: 'Field_1'}"
```

---

### Example 4: View polygon.yaml Format

```yaml
polygons:
  Field_1:
    - [0.99, -3.44, 0.0]
    - [-2.41, -3.54, 0.0]
    - [-2.31, -0.65, 0.0]
    - [0.60, -1.07, 0.0]
  
  Field_2:
    - [0.69, -3.77, 0.0]
    - [-2.90, -3.37, 0.0]
    - [0.40, -1.22, 0.0]
    - [-2.50, -0.74, 0.0]
```

Add new polygons by editing this file and restarting polygon_manager_node.

---

## Troubleshooting

### "Polygon not found" Error

**Solution**: 
1. Check polygon exists in `config/polygon.yaml`
2. Verify polygon_manager_node is running
3. List polygons: `ros2 service call /polygon_manager/list_polygons polygon_interfaces/srv/ListPolygons`

### "NavigateToPose failed with status 6"

**Cause**: Timer was still sending duplicate goals (race condition)
**Solution**: Already fixed - timer is cancelled after first goal

### "No coverage path computed"

**Solution**:
1. Verify ComputeCoveragePath action server is running
2. Check polygon has minimum 3 points
3. Ensure bt_navigator is in 'active' state

### "Robot doesn't move"

**Solutions**:
1. Check simulation time: `ros2 param get /use_sim_time`
2. Verify map is loaded: `ros2 topic echo /map`
3. Check robot odometry: `ros2 topic echo /odom`
4. Verify controller_server is active: `ros2 topic list | grep /cmd_vel`

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Gazebo Simulator                                            │
│ ├─ warehouse.world                                         │
│ ├─ Pixel robot model                                       │
│ └─ Physics engine                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Navigation Stack (Nav2)                                     │
│ ├─ AMCL Localization                                       │
│ ├─ Map Server (warehouse_map.yaml)                         │
│ ├─ Global Planner (NavfnPlanner)                          │
│ ├─ Local Controller (RegulatedPurePursuitController)      │
│ ├─ Coverage Planner (opennav_coverage)                    │
│ └─ Behavior Tree Navigator (bt_navigator)                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Polygon Management System                                   │
│ ├─ polygon_manager_node (storage/retrieval)               │
│ ├─ polygon_recorder_server (RViz recording)               │
│ └─ config/polygon.yaml (YAML database)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Coverage Execution (execute_polygon.py)                     │
│ ├─ GetPolygon service call                                │
│ ├─ ComputeCoveragePath action                             │
│ ├─ NavigateToPose action                                  │
│ └─ FollowPath action                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Concepts

### Threading Model (polygon_recorder_server.py)

**Problem**: SingleThreadedExecutor blocks subscriber during action loop
```
SingleThreadedExecutor
  └─ Action loop while(running)
     ├─ Blocks executor (cannot process other callbacks)
     └─ /clicked_point subscriber never runs
     └─ Points never recorded ❌
```

**Solution**: MultiThreadedExecutor runs callbacks in parallel
```
MultiThreadedExecutor
  ├─ Thread 1: Action loop while(running)
  └─ Thread N: /clicked_point subscriber
     └─ Both run concurrently ✓
     └─ Points recorded while action runs ✓
```

### Single-Shot Execution (execute_polygon.py)

**Problem**: Repeating timer caused goal preemption
```
Timer fires every 0.5s
  ├─ First goal: ComputeCoveragePath ✓
  ├─ Second goal: ComputeCoveragePath (preempts navigate) ❌
  └─ Repeat infinitely...
```

**Solution**: Cancel timer after mission starts
```
Timer fires once (0.5s)
  ├─ Set execution_started = True
  ├─ Destroy timer
  └─ Single linear pipeline ✓
```

---

## Dependencies

- ROS2 Humble
- Nav2 (navigation framework)
- Gazebo (simulator)
- opennav_coverage (coverage planner)
- polygon_interfaces (custom ROS messages)
- geometry_msgs, nav_msgs, action_msgs

---

## Contributing

To add a new polygon:

1. Edit `config/polygon.yaml`
2. Add entry with at least 3 points (X, Y, Z)
3. Restart polygon_manager_node
4. Verify with: `ros2 service call /polygon_manager/list_polygons polygon_interfaces/srv/ListPolygons`

---

## License

[Add your license here]

---

**Last Updated**: May 30, 2026
**ROS2 Version**: Humble
**Robot**: Pixel (Custom UGV)
