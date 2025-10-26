# Lunabot One - Autonomous Navigation for NASA Lunabotics

Autonomous navigation system built for the NASA Lunabotics competition. Handles sandy terrain, outdoor lighting, and obstacle-rich environments using LIDAR-based SLAM with IMU drift correction.

**Key Technical Features:**
- Multi-LIDAR fusion (3x sensors, 270° coverage)
- IMU-corrected odometry prevents wheel slip drift
- SparkFlex motor control via CAN bus
- Nav2 integration with custom waypoint patterns for testing

## System Architecture

```
├── Navigation: Nav2 + SLAM Toolbox
├── Perception: 3x LIDAR fusion + IMU
├── Control: SparkFlex CAN controllers
├── Hardware: RPi5 + CAN HAT
└── Simulation: Gazebo + ROS2 Control
```

**Sensor Pipeline:**
- LIDAR data → occupancy grid mapping
- IMU → orientation correction for wheel slippage
- Encoder feedback → velocity control loop

## Prerequisites

### For Simulation (Students)
- ROS2 Jazzy
- Gazebo Garden/Harmonic
- Nav2
- SLAM Toolbox

### For Hardware Competition Robot
- All simulation prerequisites plus:
- **SparkCAN library** (install separately - see [SPARKCAN_SETUP.md](SPARKCAN_SETUP.md))
- Raspberry Pi 5 (16GB RAM)
- CAN HAT (Waveshare rs485 CAN HAT)
- 4x SparkFlex Motor Controllers (firmware 24.0.X)
- NEO Brushless motors
- 3x Lidar sensors (LDLidar LD19, RPLidar, etc.)

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for complete build guide and [HARDWARE_SETUP.md](HARDWARE_SETUP.md) for hardware configuration.

## Quick Start

### Build & Setup
```bash
make build    # Build the workspace
make source   # Source the workspace
```

### Simulation Mode 

**Start robot simulation:**
```bash
make sim      # Single command starts everything
```

**Full autonomous navigation (4 terminals):**
```bash
# Terminal 1: Start simulation
make sim

# Terminal 2: Open RViz visualization
rviz2

# Terminal 3: Start navigation stack
make full-nav

# Terminal 4: Run waypoint navigation
make arena-waypoints
```

### Hardware Mode (Still in development)

**Hardware startup:**
```bash
make hardware     # Launch robot drivers
make hardware-nav # Start navigation stack
```

**Hardware Setup Required:** See [HARDWARE_SETUP.md](HARDWARE_SETUP.md) for CAN bus configuration and SparkFlex setup.

## Past Technical Problems

**Wheel Slip on terrain**: IMU runs at 100Hz to catch wheel slip events and correct odometry drift
**Multi-LIDAR Fusion**: Coordinate transformation for 270° sensor coverage taking into account different positions of LIDARs

## Navigation Features

### Autonomous Waypoint Navigation
Navigate through predefined competition patterns:
```bash
make arena-waypoints pattern=arena_exploration
# Available: arena_exploration, arena_perimeter, zone_inspection, obstacle_navigation
```

### Manual Goal Navigation
Send the robot to specific coordinates:
```bash
python3 scripts/navigate_to_goal.py 2.5 1.0  # x, y coordinates
python3 scripts/navigate_to_goal.py 2.5 1.0 1.57  # x, y, yaw_angle
```

### Visual Features (Simulation)
- **Green waypoint markers**: Shows target locations in Gazebo
- **2-second pausing**: Robot stops at each waypoint for observation

For detailed navigation instructions, see [NAVIGATION_README.md](NAVIGATION_README.md)

## Sensors

**LIDAR**: Primary mapping sensor, 270° coverage via 3-sensor fusion
**IMU**: 100Hz orientation correction, prevents odometry drift on sandy terrain
**RGBD Camera**: Available for object detection, not used in mapping pipeline yet

*Key Topics: `/scan`, `/imu/data`, `/camera/image_raw`, `/camera/depth/points`*

### IMU-Corrected Odometry System
**Problem**: Robot loses position when wheels slip on obstacles
**Solution**: IMU provides absolute yaw orientation to correct wheel odometry

**How it works:**
- Wheel encoders → X/Y position
- IMU gyroscope → absolute heading
- Fusion → drift-resistant localization

### Viewing Sensor Data
**IMU data:**
```bash
ros2 topic echo /imu/data  # See orientation and angular velocity
```

**Camera feeds in RViz:**
- Add **Camera** display → `/camera/image_raw`
- Add **PointCloud2** display → `/camera/depth/points` 

## SLAM System

Uses **SLAM Toolbox** with **LIDAR + IMU mapping** for competition environments:

**Why LIDAR over cameras?**
- Works in lunar, dusty conditions
- No lighting issues (outdoor sun/shadows)
- Lower CPU usage than vision SLAM
- Used by most other teams 

**Configuration:**
- Map resolution: 5cm grid cells
- IMU integration: Improves loop closure detection
- Outdoor tuning: Optimized for sparse features
- Real-time performance: Efficient for competition robotics

## Launch Commands Reference

### Basic Commands
```bash
make sim           # Simulation only
make sim-nav       # Simulation + navigation
make full-nav      # Complete navigation stack
make hardware      # Hardware drivers
make hardware-nav  # Hardware + navigation
```

### Development & Testing
```bash
make arena-waypoints  # Waypoint navigation
make lidar-test      # Test LIDAR sensors
make ball-tracker    # Object detection demo
make joystick        # Manual control
```

### SLAM Mapping
Create new maps instead of using existing ones:

**Simulation:**
```bash
make sim
ros2 launch lunabot_one online_async_launch.py
rviz2
```

**Hardware:**
```bash
make hardware
ros2 launch lunabot_one online_async_launch.py
rviz2
```

**Save your map:**
```bash
ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/lunabot_one/maps/new_map
```

## Robot Control Options

**Nintendo Switch Controller**: Automatically included in simulation
**Keyboard Control**:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/diff_cont/cmd_vel_unstamped
```

## Development Status
- [DONE] Autonomous waypoint navigation working
- [DONE] SLAM mapping validated in competition arena
- [DONE] Multi-LIDAR fusion operational
- [WIP] Tuning path planning for tighter obstacle clearance
- [WIP] Testing CAN bus reliability under load

## Launch Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `use_hardware` | `false` | Switch between simulation and hardware |
| `sim_mode` | `true` | Enable simulation sensors |
| `use_ros2_control` | `true` | Use ros2_control framework |
| `world` | `obstacles.world` | Gazebo world file |

## Learning ROS2 with This Project

**New to ROS2?** This project demonstrates:
- **Nodes & Topics**: See sensor data flow with `ros2 topic list`
- **Launch Files**: Understand multi-node startup
- **Transforms**: Learn coordinate frames with `ros2 run tf2_tools view_frames`
- **Visualization**: Use RViz to see robot state and sensor data
- **Simulation**: Test algorithms safely before hardware deployment

**Useful debugging commands:**
```bash
ros2 topic list          # See all data streams
ros2 topic echo /scan    # View LIDAR data
ros2 node list          # See running components
rviz2                   # Visualize everything
```

## Quick Reference Workflows

**Learning/Development:**
```bash
make sim && rviz2 && make full-nav
```

**Competition Navigation:**
```bash
make hardware && make hardware-nav && make arena-waypoints
```

**Map Creation:**
```bash
make sim && ros2 launch lunabot_one online_async_launch.py && rviz2
```