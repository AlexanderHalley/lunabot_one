# Lunabot One - ROS2 Robot System (Simulation & Hardware)

**Complete ROS2 robot system supporting both Gazebo simulation and real hardware deployment with SLAM Toolbox + IMU navigation.**

## Prerequisites

### For Simulation
- ROS2 Jazzy
- Gazebo Garden/Harmonic
- Nav2
- SLAM Toolbox

### For Hardware 
- All simulation prerequisites plus:
- Raspberry Pi 5 (4GB+ RAM)
- CAN HAT (Waveshare/Seeed Studio)
- 4x ODrive S1 Motor Controllers
- Compatible BLDC motors
- Lidar sensor (LDLidar LD19, RPLidar, etc.)

See [HARDWARE_SETUP.md](HARDWARE_SETUP.md) for detailed hardware setup.

## Setup
1. Build the workspace:
   ```bash
   colcon build --packages-select lunabot_one --symlink-install
   ```

2. Source the workspace:
   ```bash
   source install/setup.bash
   ```

## Quick Start

### 🖥️ Simulation Mode (Default)

**Basic simulation startup:**
```bash
# Single unified launch command
ros2 launch lunabot_one unified_bringup.launch.py

# Or with specific world
ros2 launch lunabot_one unified_bringup.launch.py world:=./worlds/lunabotics_arena.world
```

**For Navigation (4-Tab Method):**

**Tab 1: Start Simulation**
```bash
ros2 launch lunabot_one unified_bringup.launch.py
```

**Tab 2: Start Navigation**
```bash
ros2 launch lunabot_one minimal_navigation_launch.py map:=/home/alexanderh/ros2_ws/src/lunabot_one/maps/saved_map.yaml
```

**Tab 3: Start RViz**
```bash
rviz2
```

**Tab 4: Set Initial Pose (Required for Navigation)**
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

### 🤖 Hardware Mode

**Basic hardware startup:**
```bash
# Launch robot hardware drivers
ros2 launch lunabot_one unified_bringup.launch.py use_hardware:=true

# Or with specific configuration
ros2 launch lunabot_one unified_bringup.launch.py use_hardware:=true sim_mode:=false
```

**For Navigation with hardware:**
```bash
# Tab 1: Hardware bringup
ros2 launch lunabot_one unified_bringup.launch.py use_hardware:=true

# Tab 2: Hardware navigation 
ros2 launch lunabot_one hardware_navigation.launch.py

# Tab 3: RViz
rviz2

# Tab 4: Set initial pose (same as simulation)
```

**⚠️ Hardware Setup Required:** See [HARDWARE_SETUP.md](HARDWARE_SETUP.md) for complete hardware setup instructions including CAN bus configuration and ODrive setup.

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

## Launch Modes & Options

### 🎛️ Launch Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `use_hardware` | `false` | Switch between simulation and hardware |  
| `sim_mode` | `true` | Enable simulation sensors (depth camera, IMU) |
| `use_ros2_control` | `true` | Use ros2_control framework |
| `world` | `obstacles.world` | World file for simulation |

### 📋 Common Launch Commands

```bash
# Basic simulation (default)
ros2 launch lunabot_one unified_bringup.launch.py

# Simulation with different world
ros2 launch lunabot_one unified_bringup.launch.py world:=./worlds/lunabotics_arena.world

# Hardware mode
ros2 launch lunabot_one unified_bringup.launch.py use_hardware:=true

# Hardware without simulation sensors
ros2 launch lunabot_one unified_bringup.launch.py use_hardware:=true sim_mode:=false
```

### 🗺️ SLAM/Mapping Mode
Create new maps instead of using existing ones:

**Simulation SLAM:**
```bash
ros2 launch lunabot_one unified_bringup.launch.py
ros2 launch lunabot_one online_async_launch.py
rviz2
```

**Hardware SLAM:**
```bash
ros2 launch lunabot_one unified_bringup.launch.py use_hardware:=true
ros2 launch lunabot_one online_async_launch.py
rviz2  
```

**Save map:**
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

## 🚀 Quick Reference

**🖥️ Simulation Navigation:**
```bash
# 4 terminals:
ros2 launch lunabot_one unified_bringup.launch.py
ros2 launch lunabot_one minimal_navigation_launch.py map:=./maps/saved_map.yaml
rviz2
ros2 topic pub --once /initialpose [...]

# Navigate:
python3 scripts/navigate_to_goal.py 2.0 1.0
```

**🤖 Hardware Navigation:**
```bash
# 4 terminals:
ros2 launch lunabot_one unified_bringup.launch.py use_hardware:=true
ros2 launch lunabot_one hardware_navigation.launch.py
rviz2  
ros2 topic pub --once /initialpose [...]

# Navigate:
python3 scripts/navigate_to_goal.py 2.0 1.0
```

**🗺️ SLAM Mapping:**
```bash
# Simulation:
ros2 launch lunabot_one unified_bringup.launch.py
ros2 launch lunabot_one online_async_launch.py
rviz2

# Hardware:
ros2 launch lunabot_one unified_bringup.launch.py use_hardware:=true
ros2 launch lunabot_one online_async_launch.py  
rviz2
```

## SLAM System

The robot uses **SLAM Toolbox** with **lidar + IMU mapping** optimized for lunabotics competition environments:

### Key Features
- **Lidar + IMU mapping**: Uses `/scan` topic from lidar and `/imu/data` for improved orientation
- **Outdoor optimized**: Parameters tuned for sandy terrain and sparse outdoor features  
- **Real-time performance**: Lightweight and efficient for competition robotics
- **Nav2 integration**: Seamless compatibility with ROS2 navigation stack
- **IMU integration**: Enhances loop closure detection and reduces drift during rotational movements

### SLAM Configuration
- **Config file**: `config/params/mapper_params_online_async.yaml`
- **Launch file**: `launch/online_async_launch.py`
- **Topics used**: `/scan` (lidar), `/odom` (wheel odometry), `/imu/data` (inertial measurement)
- **Map resolution**: 0.05m (5cm grid cells)
- **Loop closure**: Enabled with competition-appropriate thresholds
- **IMU sensor**: 100Hz update rate with realistic noise modeling

### Why Lidar + IMU SLAM?
For lunabotics competition:
- **Reliability**: Lidar works in sandy, dusty environments where cameras struggle
- **Lighting independence**: No issues with outdoor sun, shadows, or glare  
- **IMU advantages**: Improves orientation tracking during wheel slip on sand
- **Enhanced loop closure**: IMU helps detect when returning to previous locations
- **Computational efficiency**: Lower CPU usage than vision-based SLAM
- **Proven approach**: Used by successful competition teams

The camera remains available for computer vision tasks (object detection, visual servoing) but is not used for mapping.

## IMU Sensor

The robot includes a high-frequency IMU sensor that provides inertial measurements for improved SLAM performance.

### IMU Topics
- `/imu/data` - IMU measurements (sensor_msgs/msg/Imu) including:
  - **Linear acceleration**: 3-axis acceleration including gravity
  - **Angular velocity**: 3-axis rotational rates  
  - **Orientation**: Quaternion orientation estimate

### IMU Features
- **Update Rate**: 100 Hz for responsive motion tracking
- **Realistic Noise**: Gaussian noise modeling for accurate simulation
  - Angular velocity noise: ±0.0002 rad/s standard deviation
  - Linear acceleration noise: ±0.017 m/s² standard deviation
- **Frame**: `imu_link` attached to robot chassis
- **SLAM Integration**: Automatically used by SLAM Toolbox when `use_imu: true`

### Viewing IMU Data
**In RViz2:**
1. Add **Imu** display
2. Set Topic to `/imu/data`
3. Shows orientation arrow and acceleration vector

**Command Line:**
```bash
ros2 topic echo /imu/data
```

When stationary, you should see:
- Small random angular velocities (noise around 0)
- Linear acceleration Z-axis ~9.8 m/s² (gravity)
- Stable orientation quaternion

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