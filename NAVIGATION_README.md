# Lunabot One - ROS2 Navigation Setup

**TODO:** Tune odometry, nav2 parameters, and simplify launch files

This guide provides complete instructions for setting up autonomous navigation with the Lunabot One robot using ROS2 Nav2 stack.

## Prerequisites

- ROS2 Jazzy installed
- Gazebo simulation environment
- Nav2 navigation stack
- Workspace built and sourced

## Quick Start - 4-Tab Setup

### Tab 1: Build and Launch Simulation
```bash
cd ~/ros2_ws
colcon build --packages-select lunabot_one --symlink-install
source install/setup.bash
ros2 launch lunabot_one simulation.launch.py
```

### Tab 2: Launch Navigation
```bash
cd ~/ros2_ws
source install/setup.bash
ros2 launch lunabot_one minimal_navigation_launch.py map:=/home/alexanderh/ros2_ws/src/lunabot_one/maps/saved_map.yaml
```

### Tab 3: Launch RViz for Visualization
```bash
cd ~/ros2_ws
source install/setup.bash
rviz2
```

### Tab 4: Set Initial Pose
```bash
ros2 topic pub --once /initialpose geometry_msgs/PoseWithCovarianceStamped '{
  header: {frame_id: "map"},
  pose: {
    pose: {
      position: {x: 0.0, y: 0.0, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    },
    covariance: [0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.06853892326654787]
  }
}'
```

## Navigation Methods

### Method 1: Python Script (Recommended)
Use the automated navigation script:

```bash
cd ~/ros2_ws
source install/setup.bash
python3 src/lunabot_one/scripts/navigate_to_goal.py <x> <y> [yaw_angle]
```

**Examples:**
```bash
# Navigate to coordinates (2.5, 1.0)
python3 src/lunabot_one/scripts/navigate_to_goal.py 2.5 1.0

# Navigate to coordinates (3.0, -1.5) with specific orientation (1.57 radians = 90 degrees)
python3 src/lunabot_one/scripts/navigate_to_goal.py 3.0 -1.5 1.57
```

### Method 2: Manual Commands
For advanced users who want to see the individual steps:

**Step 1: Compute Path**
```bash
ros2 action send_goal /compute_path_to_pose nav2_msgs/action/ComputePathToPose '{
  goal: {
    header: {frame_id: "map"},
    pose: {
      position: {x: 2.0, y: 1.0, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    }
  },
  planner_id: "",
  use_start: false
}'
```

**Step 2: Execute Path**
```bash
ros2 action send_goal /follow_path nav2_msgs/action/FollowPath '{
  path: [COPY_PATH_FROM_STEP_1_RESULT]
}'
```

## Using RViz for Goal Selection

1. In RViz, use the "2D Goal Pose" tool to visually select a goal
2. Check the RViz output for coordinates like:
   ```
   [INFO] [rviz2]: Setting goal pose: Frame:map, Position(3.34933, 1.52105, 0), Orientation(0, 0, 0.528408, 0.848991) = Angle: 1.11345
   ```
3. Use these coordinates with the Python script:
   ```bash
   python3 src/lunabot_one/scripts/navigate_to_goal.py 3.34933 1.52105 1.11345
   ```

## Configuration Files

### Key Configuration Files
- `config/params/nav2_params.yaml` - Main navigation parameters
- `config/params/mapper_params_online_async.yaml` - SLAM/mapping parameters  
- `config/rviz/main.rviz` - RViz configuration
- `maps/saved_map.yaml` - Map metadata
- `maps/saved_map.pgm` - Map image data

### Important Parameters
- **Lidar range**: 12.0m (realistic range)
- **Robot radius**: 0.22m
- **Wheel separation multiplier**: 1.1111 (for odometry accuracy)
- **Controller frequency**: 20.0 Hz
- **Map resolution**: 0.05m/pixel

## Troubleshooting

### Common Issues

**1. "No path found" error**
- Goal may be in obstacle/wall area on map
- Try goals closer to current robot position
- Check RViz to ensure goal is in free space (white areas)

**2. Robot not moving**
- Verify initial pose is set correctly
- Check that /amcl_pose topic is publishing
- Ensure map->odom transform exists

**3. Transform errors**
- Make sure all launch files are running
- Verify initial pose was set after launching navigation

**4. RViz "2D Goal Pose" not working automatically**  
- This is expected with minimal navigation setup
- Use the Python script or manual commands instead

### Useful Debug Commands

```bash
# Check robot's current position
ros2 topic echo /amcl_pose --once

# View available topics
ros2 topic list

# Check transform tree
ros2 run tf2_tools view_frames

# Monitor navigation status
ros2 topic echo /planner_server/transition_event
```

## System Architecture

### Navigation Stack Components
- **AMCL**: Adaptive Monte Carlo Localization for robot positioning
- **Map Server**: Serves the pre-created map
- **Planner Server**: Computes paths using NavFn planner
- **Controller Server**: Executes paths using DWB local planner
- **Velocity Smoother**: Smooths velocity commands

### Launch Files
- `simulation.launch.py`: Gazebo simulation + robot
- `minimal_navigation_launch.py`: Navigation stack without bt_navigator
- `navigation_launch.py`: Full Nav2 stack (has bt_navigator issues)

### Custom Scripts
- `scripts/navigate_to_goal.py`: Automated navigation helper

## Creating New Maps

To create a new map for navigation:

1. Launch simulation and SLAM:
```bash
ros2 launch lunabot_one simulation.launch.py
ros2 launch lunabot_one online_async_launch.py
```

2. Drive around to explore the environment

3. Save the map:
```bash
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/lunabot_one/maps/new_map
```

## Hardware Configuration

### Robot Specifications  
- **Differential drive**: 4-wheel robot with front/rear wheel pairs
- **Lidar sensor**: 360° laser scanner, 12m range
- **Base dimensions**: 0.44m radius for collision checking
- **Max velocity**: 0.26 m/s linear, 1.0 rad/s angular

### Sensor Topics
- `/scan`: Lidar data (LaserScan)
- `/odom`: Odometry data (Odometry)
- `/imu/data`: IMU measurements (Imu) - used by SLAM Toolbox
- `/cmd_vel`: Velocity commands (Twist)

## Performance Notes

- Navigation works reliably for goals within 3-4 meters
- Complex paths through narrow passages may require parameter tuning
- Odometry accuracy improved with wheel_separation_multiplier = 1.1111
- System tested with Gazebo simulation in obstacle-rich environments

## Robot Control Options (Alternative to Navigation)

### Nintendo Switch Controller
The controller support is automatically included in the simulation launch.

### Keyboard Teleop
For manual keyboard control instead of autonomous navigation:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/diff_cont/cmd_vel_unstamped
```

---

## Quick Reference Commands

```bash
# Complete setup (4 commands in 4 tabs)
ros2 launch lunabot_one simulation.launch.py
ros2 launch lunabot_one minimal_navigation_launch.py map:=./maps/saved_map.yaml  
rviz2
ros2 topic pub --once /initialpose geometry_msgs/PoseWithCovarianceStamped [...]

# Navigate to goal
python3 scripts/navigate_to_goal.py 2.0 1.0

# Check robot position  
ros2 topic echo /amcl_pose --once
```