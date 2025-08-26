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

## RGBD Depth Camera

The robot includes a working RGBD depth camera that provides both color and depth information for mapping and navigation.

### Camera Topics
- `/camera/image_raw` - RGB color image feed (sensor_msgs/msg/Image)
- `/camera/depth/image_raw` - Depth image (sensor_msgs/msg/Image) 
- `/camera/depth/points` - 3D point cloud (sensor_msgs/msg/PointCloud2)
- `/camera/camera_info` - Camera calibration parameters (sensor_msgs/msg/CameraInfo)

### Viewing Camera Feeds

**RGB Image in RViz2:**
1. Add **Camera** display
2. Set Image Topic to `/camera/image_raw`
3. Color image will appear in display panel

**Depth Image in RViz2:**
1. Add **Image** display  
2. Set Image Topic to `/camera/depth/image_raw`
3. **Important**: Turn OFF "Normalize Range"
4. Set **Min Value**: 0.05, **Max Value**: 8.0
5. Depth shows as grayscale (closer = darker, farther = lighter)

**Point Cloud in RViz2:**
1. Add **PointCloud2** display
2. Set Topic to `/camera/depth/points`
3. Set **Fixed Frame** to `base_link` or `map`
4. Set **Size (m)** to `0.02` for better visibility
5. **Color Transformer**: Use `Z` (height-based colors)
6. Shows 3D representation of depth data

**In Gazebo:**
1. Right-click → Plugins → Image Display
2. Subscribe to `camera/image` for RGB view
3. Subscribe to `camera/depth_image` for depth view

### Camera Specifications
- **Resolution:** 640x480 (both RGB and depth)
- **Update Rate:** 10 Hz
- **Field of View:** 1.089 radians (~62.4 degrees)
- **Depth Range:** 0.05m to 8.0m
- **Position:** Front of chassis, centered between front wheels
- **Visual Indicator:** Blue rectangular camera box

### Switching Between RGB and Depth Cameras

**To use RGB Camera only:**
```xml
<!-- In description/robot.urdf.xacro -->
<xacro:include filename="camera.xacro" />
<!-- <xacro:include filename="depth_camera.xacro" /> -->
```

**To use Depth Camera (current):**
```xml 
<!-- In description/robot.urdf.xacro -->
<!-- <xacro:include filename="camera.xacro" /> -->
<xacro:include filename="depth_camera.xacro" />
```

**Visual Differences:**
- **RGB Camera**: Red rectangular box
- **Depth Camera**: Blue rectangular box

### Technical Details
- Uses `rgbd_camera` sensor type in Gazebo Harmonic
- RGB/depth images bridged via `ros_gz_image_bridge`
- Point clouds bridged via `ros_gz_bridge` 
- Frame: `camera_link` for point cloud, `camera_link_optical` for images
- All bridges configured in `launch/simulation.launch.py`