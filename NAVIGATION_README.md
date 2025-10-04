# Navigation Guide

Autonomous navigation workflows for the Lunabot One system.

## Prerequisites
- Main system running: `make sim` or `make hardware`
- RViz visualization: `rviz2`

## Coordinate System

**Arena Layout:**
- **Origin (0,0)**: Bottom-left corner of competition arena
- **Robot spawn**: (1,1) - robot starts 1 meter from bottom-left corner
- **X-axis**: Increases toward right side of arena
- **Y-axis**: Increases toward top of arena
- **Orientation**: 0 radians faces positive X direction (right)

**Example coordinates:**
```bash
python3 scripts/navigate_to_goal.py 1.0 1.0     # Starting position
python3 scripts/navigate_to_goal.py 5.0 3.0     # Center-right of arena
python3 scripts/navigate_to_goal.py 2.0 6.0     # Upper area
python3 scripts/navigate_to_goal.py 0.5 0.5     # Near origin corner
```

## Navigation Methods

### Autonomous Waypoints (Recommended)
Navigate through predefined competition patterns:
```bash
make arena-waypoints pattern=arena_exploration
# Available patterns: arena_exploration, arena_perimeter, zone_inspection, obstacle_navigation
```

### Manual Goal Navigation
Send the robot to specific coordinates:
```bash
python3 scripts/navigate_to_goal.py 2.5 1.0          # x, y coordinates
python3 scripts/navigate_to_goal.py 2.5 1.0 1.57     # x, y, yaw_angle (radians)
```

### RViz Goal Selection
1. Use "2D Goal Pose" tool in RViz to visually select target
2. Check console output for coordinates:
   ```
   Setting goal pose: Position(3.34, 1.52, 0), Angle: 1.11
   ```
3. Use coordinates with navigation script:
   ```bash
   python3 scripts/navigate_to_goal.py 3.34 1.52 1.11
   ```

## Mapping vs Localization

### SLAM Mapping (Create New Maps)
Use when exploring unknown environments:
```bash
make sim
ros2 launch lunabot_one online_async_launch.py
rviz2
# Drive around to map environment, then save:
ros2 run nav2_map_server map_saver_cli -f maps/new_map
```

### AMCL Localization (Use Existing Maps)
Use for navigation on known maps (more efficient):
```bash
make sim
ros2 launch lunabot_one localization_launch.py map:=maps/arena_map.yaml
# Set initial pose in RViz using "2D Pose Estimate" tool
make arena-waypoints
```

**When to use each:**
- **SLAM Mapping**: Unknown environments, competition scouting, map creation
- **AMCL Localization**: Known environments, competition runs, better performance

## Complete Workflows

### Competition Navigation Workflow
```bash
# Terminal 1: Start simulation
make sim

# Terminal 2: Open visualization
rviz2

# Terminal 3: Start navigation stack
make full-nav

# Terminal 4: Execute waypoint mission
make arena-waypoints pattern=arena_exploration
```

### Manual Navigation Workflow
```bash
# After completing steps 1-3 above:
python3 scripts/navigate_to_goal.py 2.0 1.5
python3 scripts/navigate_to_goal.py -1.0 2.0 3.14
```

## Troubleshooting

### Robot Won't Move
**Check localization:**
```bash
ros2 topic echo /amcl_pose --once  # Should show current position
```

**Verify transforms:**
```bash
ros2 run tf2_tools view_frames      # Check map->odom->base_link chain
```

**Check navigation status:**
```bash
ros2 topic echo /planner_server/transition_event
```

### Path Planning Fails
- **"No path found"**: Goal may be in obstacle area (red/black in RViz)
- **Robot stuck**: Try goals closer to current position
- **Transform errors**: Ensure initial pose is set after launching navigation

### Common Issues
1. **Goal in obstacle**: Check RViz costmap - goals must be in free space (white areas)
2. **No initial pose**: Set using "2D Pose Estimate" tool in RViz
3. **Missing transforms**: Restart navigation launch file
4. **RViz "2D Goal Pose" not working**: Expected - use Python scripts instead

## System Architecture

### Navigation Stack Components
- **AMCL**: Robot localization using particle filter
- **Map Server**: Serves pre-built maps to navigation stack
- **Planner Server**: Global path planning (NavFn planner)
- **Controller Server**: Local path execution (DWB controller)
- **Velocity Smoother**: Smooths velocity commands for hardware

### Key Topics
- `/scan`: LIDAR data for obstacle detection
- `/odom`: Wheel odometry for motion estimation
- `/imu/data`: IMU data for orientation correction
- `/cmd_vel`: Velocity commands to robot
- `/amcl_pose`: Current robot position estimate

## Configuration

### Navigation Parameters
- **Robot radius**: 0.44m for collision checking
- **Max linear velocity**: 0.26 m/s
- **Max angular velocity**: 1.0 rad/s
- **Controller frequency**: 20 Hz
- **Planner frequency**: 1 Hz

### Key Configuration Files
- `config/params/nav2_params.yaml` - Navigation stack parameters
- `config/params/mapper_params_online_async.yaml` - SLAM configuration
- `maps/arena_map.yaml` - Competition arena map metadata

### Performance Tuning
- **Wheel separation multiplier**: 1.1111 (improves odometry accuracy)
- **LIDAR range**: 12.0m (realistic sensor limit)
- **Map resolution**: 0.05m/pixel (5cm grid cells)
- **Particle count**: Tuned for balance of accuracy vs performance

## Robot Control Alternatives

### Nintendo Switch Controller
Automatically available in simulation:
```bash
make sim  # Controller support included
```

### Keyboard Teleop
Manual keyboard control:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/diff_cont/cmd_vel_unstamped
```

## Performance Notes

- Navigation tested reliable for goals within 5-6 meters
- Complex paths through narrow passages may require parameter tuning
- System validated in obstacle-rich competition-style environments
- Multi-LIDAR fusion provides robust obstacle detection in 270° arc

## Debug Commands

```bash
# Monitor robot position
ros2 topic echo /amcl_pose --once

# View all active topics
ros2 topic list

# Check navigation node status
ros2 node list | grep nav

# Monitor velocity commands
ros2 topic echo /cmd_vel

# View costmap for path planning
ros2 topic echo /global_costmap/costmap
```