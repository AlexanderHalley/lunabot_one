# SparkCAN Integration Guide

This document describes the integration of the sparkcan library for SparkFlex motor controller communication.

## Architecture Overview

### Previous Architecture (Removed)
- ❌ ros2_control framework
- ❌ SparkFlex ROS2 Control Hardware Interface (didn't exist)
- ❌ socketcan_interface
- ❌ Complex YAML configuration files

### Current Architecture (sparkcan-based)
```
ROS2 Navigation Stack
    ↓
SparkFlex Driver Node (sparkflex_driver_node.cpp)
    ↓
sparkcan Library (C++ CAN interface)
    ↓
Linux SocketCAN
    ↓
CAN HAT Hardware
    ↓
SparkFlex Motor Controllers (CAN IDs 1-4)
```

## Key Components

### 1. SparkFlex Driver Node
**File**: `src/sparkflex_driver_node.cpp`

A custom ROS2 node that:
- Subscribes to `/cmd_vel` (Twist messages)
- Publishes odometry to `/odom`
- Publishes joint states to `/joint_states`
- Directly communicates with SparkFlex controllers via sparkcan
- Handles differential drive kinematics
- Sends periodic heartbeat to keep motors alive (50 Hz)

**Key Features**:
- Velocity control mode (RPM-based)
- Automatic unit conversions (m/s ↔ RPM, rotations ↔ radians)
- Configurable via ROS2 parameters
- Error handling with throttled logging

### 2. SparkCAN Library
**Package**: `sparkcan` (external dependency)

Provides:
- `SparkFlex` class for motor control
- `CANInterface` for CAN bus communication
- Control modes: DUTY_CYCLE, VELOCITY, POSITION, VOLTAGE, CURRENT
- Motor configuration: PID tuning, current limits, idle modes
- Feedback: position, velocity, current, temperature, faults

**Important**: Only works with SparkFlex firmware 24.0.X (NOT 25.0.X)

### 3. Configuration
**Launch File**: `launch/hardware_bringup.launch.py`

All configuration is done via ROS2 parameters:
```python
parameters=[
    {'can_interface': 'can0'},
    {'wheel_separation': 0.7620},  # 30 inches
    {'wheel_radius': 0.1778},      # 7 inch wheels
    {'max_rpm': 5700.0},           # NEO motor limit
    {'current_limit': 40},         # Amps
    {'pid_p': 0.0001},
    {'pid_ff': 0.000176},
    # Motor CAN IDs
    {'front_left_id': 1},
    {'front_right_id': 2},
    {'rear_left_id': 3},
    {'rear_right_id': 4}
]
```

## Motor Configuration

### SparkFlex Settings (via REV Hardware Client)
Before CAN deployment, configure each controller:
1. **CAN ID**: 1 (FL), 2 (FR), 3 (RL), 4 (RR)
2. **Motor Type**: Brushless (for NEO motors)
3. **Idle Mode**: Brake
4. **Current Limit**: 40A
5. **Firmware**: 24.0.X (use REV Hardware Client to downgrade if needed)

### Runtime Configuration (via Driver Node)
On startup, the driver node configures:
- PID gains (P, I, D, FF)
- Output range (-1.0 to 1.0)
- Current limits
- Motor inversion (right side inverted for differential drive)
- Conversion factors

## Differential Drive Kinematics

### Command → Motor RPM
```cpp
// Input: linear velocity (m/s), angular velocity (rad/s)
left_vel = linear - (angular * wheel_separation / 2.0)
right_vel = linear + (angular * wheel_separation / 2.0)

// Convert m/s to RPM
left_rpm = (left_vel / (2π * wheel_radius)) * 60
right_rpm = (right_vel / (2π * wheel_radius)) * 60
```

### Motor Feedback → Odometry
```cpp
// Read RPM from motors
left_rpm = average(FL, RL)
right_rpm = average(FR, RR)

// Convert RPM to m/s
left_vel = (left_rpm / 60) * (2π * wheel_radius)
right_vel = (right_rpm / 60) * (2π * wheel_radius)

// Calculate robot motion
linear_vel = (left_vel + right_vel) / 2
angular_vel = (right_vel - left_vel) / wheel_separation

// Integrate to get pose
x += linear_vel * cos(theta) * dt
y += linear_vel * sin(theta) * dt
theta += angular_vel * dt
```

## Communication Protocol

### Heartbeat (50 Hz)
```cpp
fl_motor_->heartbeat();
fr_motor_->heartbeat();
bl_motor_->heartbeat();
br_motor_->heartbeat();
```
**Critical**: Motors must receive periodic heartbeat or they will disable

### Velocity Commands
```cpp
fl_motor_->set(rpm_value, ControlType::VELOCITY);
```

### Feedback Reading
```cpp
double rpm = motor->getVelocity();        // RPM
double pos = motor->getPosition();        // Rotations
double current = motor->getOutputCurrent(); // Amps
double temp = motor->getMotorTemperature(); // Celsius
```

## Troubleshooting

### Build Issues
```bash
# Ensure sparkcan is installed
sudo apt install sparkcan

# Rebuild with verbose output
cd ~/ros2_ws
colcon build --packages-select lunabot_one --cmake-args -DCMAKE_VERBOSE_MAKEFILE=ON
```

### Runtime Issues

**Motors not responding:**
- Check firmware version (must be 24.0.X)
- Verify CAN bus is up: `ip link show can0`
- Monitor CAN traffic: `candump can0`
- Check node output for sparkcan errors

**Poor odometry:**
- Verify wheel_separation and wheel_radius parameters
- Check for wheel slippage
- Ensure motors are returning valid velocity feedback

**Communication errors:**
- Verify CAN bitrate matches (1 Mbps)
- Check CAN HAT connections
- Ensure proper CAN termination resistors

## Files Modified/Created

### New Files
- `src/sparkflex_driver_node.cpp` - Main driver implementation
- `hardware/SPARKCAN_INTEGRATION.md` - This document

### Modified Files
- `CMakeLists.txt` - Added C++ compilation, sparkcan dependency
- `package.xml` - Replaced ros2_control dependencies with sparkcan
- `launch/hardware_bringup.launch.py` - New launch with sparkcan driver
- `HARDWARE_SETUP.md` - Updated for SparkFlex (removed ODrive references)
- `hardware/can/can_setup.sh` - Updated comments

### Deprecated/Unused Files
- `urdf/lunabot_hardware.urdf.xacro` - ros2_control config (not used)
- `config/control/hardware/hardware_controllers.yaml` - (not used)
- `hardware/sparkflex/motor_params.yaml` - (replaced by launch params)
- `hardware/can/sparkflex_can_ids.yaml` - (replaced by launch params)

## Future Improvements

### Potential Enhancements
1. **Parameter file**: Move parameters from launch file to YAML config
2. **Dynamic reconfigure**: Add ability to tune PID gains at runtime
3. **Diagnostics**: Publish motor temperatures, currents, faults
4. **Safety**: Implement emergency stop and fault handling
5. **Acceleration limiting**: Add smoother velocity ramping
6. **Current monitoring**: Log and alert on high current draw

### Performance Tuning
- Adjust PID gains for smoother motion
- Tune odometry covariance values
- Optimize update rates for computational efficiency
- Add velocity filtering for smoother odometry

## References

- [sparkcan GitHub](https://github.com/grayson-arendt/sparkcan)
- [REV Hardware Client](https://docs.revrobotics.com/rev-hardware-client/)
- [SparkFlex Documentation](https://docs.revrobotics.com/sparkmax/)
