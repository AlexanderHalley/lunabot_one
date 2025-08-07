# Lunabot One - ROS2 Robot Simulation & Navigation

## Prerequisites
- ROS2 Jazzy
- Gazebo
- Nav2

## Setup
1. Build the workspace:
   ```bash
   colcon build --packages-select lunabot_one --symlink-install
   ```

2. Source the workspace:
   ```bash
   source install/setup.bash
   ```

## Quick Navigation Setup (4-Tab Method)

### Tab 1: Start the Simulation
Launch the robot in Gazebo simulation (includes Nintendo Switch controller support):
```bash
ros2 launch lunabot_one simulation_launch.py
```

### Tab 2: Start Navigation
In a new terminal, launch the navigation stack with your map:
```bash
ros2 launch lunabot_one minimal_navigation_launch.py map:=/home/alexanderh/ros2_ws/src/lunabot_one/maps/saved_map.yaml
```

### Tab 3: Start RViz for Visualization
In a new terminal, launch RViz to visualize the robot and map:
```bash
rviz2
```

### Tab 4: Set Initial Pose (Required for Navigation)
After launching navigation, set the robot's initial position:
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

## Autonomous Navigation

Once setup is complete, navigate to goals using the Python script:
```bash
python3 scripts/navigate_to_goal.py <x> <y> [yaw_angle]
```

Example:
```bash
python3 scripts/navigate_to_goal.py 2.5 1.0
```

For detailed navigation instructions, see [NAVIGATION_README.md](NAVIGATION_README.md)

## Alternative Launch Methods

### For SLAM/Mapping (Create New Maps)
If you want to create new maps instead of using existing ones:

1. **Terminal 1 - Simulation:**
   ```bash
   ros2 launch lunabot_one simulation_launch.py
   ```

2. **Terminal 2 - SLAM:**
   ```bash
   ros2 launch lunabot_one slam_launch.py
   ```

3. **Terminal 3 - Visualization:**
   ```bash
   rviz2
   ```

4. **Drive around to map, then save:**
   ```bash
   ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/lunabot_one/maps/new_map
   ```

## Robot Control Options

### Nintendo Switch Controller (Default)
The controller support is automatically included in the simulation launch.

### Keyboard Teleop (Alternative)
For keyboard control instead of autonomous navigation:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/diff_cont/cmd_vel_unstamped
```

## Quick Reference

**For Navigation (Recommended):**
```bash
# 4 terminals:
ros2 launch lunabot_one simulation_launch.py
ros2 launch lunabot_one minimal_navigation_launch.py map:=./maps/saved_map.yaml
rviz2
ros2 topic pub --once /initialpose [...]

# Then navigate:
python3 scripts/navigate_to_goal.py 2.0 1.0
```

**For Mapping:**
```bash
# 3 terminals:
ros2 launch lunabot_one simulation_launch.py
ros2 launch lunabot_one slam_launch.py
rviz2
```