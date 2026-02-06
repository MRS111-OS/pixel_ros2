# momentum_polygon

ROS 2 package for recording, managing, and executing coverage missions on polygons using opennav_coverage.

## Features

- **Record polygons interactively** from RViz using clicked points
- **Store polygons** in YAML format (config/polygons.yaml)
- **Feed polygons** to opennav_coverage for autonomous coverage navigation
- **2D polygon support** (x, y coordinates only)

## Package Contents

### Nodes

1. **polygon_recorder_server** - Action server for recording polygons
2. **polygon_manager_node** - Manages stored polygons
3. **cover_area.py** - Client to send polygons to opennav_coverage

### Action Interface

- `RecordPolygon.action` - Records polygon from RViz clicked points

## Installation

```bash
cd ~/pixel_ws
colcon build --packages-select momentum_polygon
source install/setup.bash
```

## Usage

### 1. Start the Polygon System

Launch the polygon recorder and manager nodes:

```bash
ros2 launch momentum_polygon polygon_system.launch.py
```

### 2. Record a Polygon in RViz

In RViz, use the **Publish Point** tool (or similar) to click points on the map.

Start recording via action client:

```bash
ros2 action send_goal /record_polygon momentum_polygon/action/RecordPolygon "{polygon_name: 'field1'}"
```

Click **3 or more points** in RViz. The polygon will automatically save after 3 points are recorded.

The polygon is saved to `config/polygons.yaml`.

### 3. Execute Coverage Mission

Send the recorded polygon to opennav_coverage:

```bash
ros2 run momentum_polygon cover_area.py field1
```

This will:
- Load the polygon named "field1" from config/polygons.yaml
- Convert it to `geometry_msgs/Polygon` format
- Send it to the `navigate_complete_coverage` action server
- Monitor progress with feedback

## Configuration

### Polygon Storage Format

Polygons are stored in `config/polygons.yaml`:

```yaml
polygons:
  field1:
    - [1.0, 2.0]
    - [4.0, 2.0]
    - [4.0, 5.0]
    - [1.0, 5.0]
    - [1.0, 2.0]  # Automatically closed
```

### Launch Parameters

```bash
ros2 launch momentum_polygon polygon_system.launch.py yaml_path:=/custom/path/polygons.yaml
```

## Integration with opennav_coverage

The `cover_area.py` client sends polygons using the `NavigateCompleteCoverage` action from opennav_coverage_msgs.

**Goal message structure:**
```python
goal_msg.polygons = [polygon]  # geometry_msgs/Polygon[]
goal_msg.frame_id = 'map'
```

## Dependencies

- ROS 2 Humble
- geometry_msgs
- opennav_coverage_msgs
- rclpy
- PyYAML

## Key Changes from polygon_feed

1. **Package renamed** to momentum_polygon
2. **No Z values stored** - only 2D coordinates (x, y)
3. **Direct integration** with opennav_coverage
4. **Simplified storage** in config/polygons.yaml

## Troubleshooting

**Action server not available:**
- Ensure `polygon_system.launch.py` is running
- Check with: `ros2 action list`

**Polygon not found:**
- Verify polygon name in `config/polygons.yaml`
- Check available polygons in logs when running cover_area.py

**opennav_coverage action server not available:**
- Ensure opennav_coverage navigation stack is running
- Check with: `ros2 action list | grep navigate_complete_coverage`

## Example Workflow

```bash
# Terminal 1: Start polygon system
ros2 launch momentum_polygon polygon_system.launch.py

# Terminal 2: Start recording (then click points in RViz)
ros2 action send_goal /record_polygon momentum_polygon/action/RecordPolygon "{polygon_name: 'my_field'}"

# Terminal 3: Execute coverage
ros2 run momentum_polygon cover_area.py my_field
```

## License

TODO: License declaration

## Maintainer

gagasaga (gangasagar4012@gmail.com)
