# TODO - Lunabot One Navigation Improvements

## High Priority Issues

### 1. Waypoint Navigation System
- **Status**: Basic waypoint navigation implemented but needs refinement
- **Issues**:
  - Waypoint execution timing needs optimization
  - Error handling for failed waypoints
  - Better integration with navigation stack
- **Files**: `scripts/arena_waypoints.py`, `launch/waypoint_navigation.launch.py`

### 2. Lidar Sensor Height Adjustment
- **Status**: Critical for obstacle detection
- **Issue**: Lidar mounted too high to detect arena boulders and small obstacles
- **Solution**: Lower lidar sensor in URDF to improve ground-level obstacle detection
- **Files**: `description/lidar.xacro`
- **Impact**: Essential for competition environment navigation

### 3. Full Navigation Launch Integration
- **Status**: Needs investigation
- **Issue**: `navigation_launch.py` or full nav2 launch not working properly
- **Current workaround**: Using `minimal_navigation_launch.py`
- **Goal**: Get complete nav2 stack working with bt_navigator
- **Files**: `launch/navigation_launch.py`

## Medium Priority Improvements

### 4. Map Coordinate System
- **Status**: Resolved for arena_map
- **Note**: Map origin fixed to align with robot spawn position
- **Maintenance**: Ensure new maps use consistent coordinate system

### 5. AMCL Initial Pose
- **Status**: Working with automatic pose setting
- **Improvement**: Make initial pose configurable per map
- **Files**: `config/params/nav2_params.yaml`, `launch/minimal_navigation_launch.py`

### 6. Navigation Parameters Tuning
- **Status**: Basic parameters working
- **Improvement**: Optimize for lunabotics competition environment
  - Tune DWB controller for sandy terrain
  - Adjust costmap parameters for outdoor environment
  - Optimize planner for longer paths
- **Files**: `config/params/nav2_params.yaml`

## Low Priority Enhancements

### 7. Hardware Integration Testing
- **Status**: Not yet tested on real hardware
- **Need**: Validate navigation stack works with actual robot hardware
- **Files**: `launch/hardware.launch.py`

### 8. RViz Configuration
- **Status**: Manual setup required
- **Improvement**: Create pre-configured RViz file for navigation
- **Files**: Create `config/rviz/navigation.rviz`

## Testing Checklist

Before considering navigation system complete:

- [ ] Waypoint navigation executes reliably
- [ ] Lidar detects all arena obstacles (boulders, walls)
- [ ] Full nav2 launch works (not just minimal)
- [ ] Navigation works on real hardware
- [ ] Path planning works for competition-length distances
- [ ] Robot can navigate around tight obstacles
- [ ] Recovery behaviors work when stuck

## Current Working Setup

**Functional navigation method:**
1. `ros2 launch lunabot_one simulation.launch.py`
2. `rviz2`
3. `ros2 launch lunabot_one minimal_navigation_launch.py map:=arena_map autoset_pose:=true`
4. `python3 scripts/arena_waypoints.py`

**Last Updated**: 2025-09-14