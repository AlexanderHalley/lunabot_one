# Build Instructions for SparkCAN Integration

## Overview

The lunabot_one package now uses the **sparkcan** library for direct CAN communication with SparkFlex motor controllers, replacing the previous ros2_control framework.

## Prerequisites

1. **ROS2 Jazzy** installed
2. **CAN hardware** (Raspberry Pi 5 with CAN HAT)
3. **4x SparkFlex motor controllers** with firmware 24.0.X

## Installation Steps

### 1. Install System Dependencies

```bash
sudo apt update
sudo apt install git cmake can-utils
```

### 2. Clone and Build SparkCAN Library

**Note**: The sparkcan library is NOT included in this repository. You must clone it separately.

```bash
# Clone sparkcan library
cd ~/ros2_ws/src
git clone https://github.com/grayson-arendt/sparkcan.git

# Build sparkcan
cd sparkcan
mkdir -p build && cd build
cmake ..
make -j$(nproc)

# Install to system (requires sudo)
sudo make install
sudo ldconfig
```

**Alternative**: Use the automated install script after cloning:
```bash
# Clone first
cd ~/ros2_ws/src
git clone https://github.com/grayson-arendt/sparkcan.git

# Build and install
cd ~/ros2_ws/src/lunabot_one
sudo ./hardware/can/install_sparkcan.sh
```

### 3. Build Lunabot Package

```bash
cd ~/ros2_ws
colcon build --packages-select lunabot_one
source install/setup.bash
```

## Running on Hardware

### 1. Setup CAN Interface

```bash
# Run CAN setup script (requires sudo)
sudo ~/ros2_ws/install/lunabot_one/share/lunabot_one/hardware/can/can_setup.sh

# Verify CAN interface is up
ip link show can0
```

### 2. Configure SparkFlex Controllers

Before first use, configure each SparkFlex controller using **REV Hardware Client**:

1. Download [REV Hardware Client](https://docs.revrobotics.com/rev-hardware-client/)
2. Connect each SparkFlex via USB
3. Set configuration:
   - **CAN ID**: 1 (FL), 2 (FR), 3 (RL), 4 (RR)
   - **Motor Type**: Brushless (for NEO motors)
   - **Idle Mode**: Brake
   - **Current Limit**: 40A
   - **Firmware**: **24.0.X** (required - NOT 25.0.X)

### 3. Launch Hardware Driver

```bash
ros2 launch lunabot_one hardware_bringup.launch.py
```

**Optional parameters**:
```bash
ros2 launch lunabot_one hardware_bringup.launch.py \
  can_interface:=can0 \
  auto_can_setup:=false \
  use_sim_time:=false
```

## Troubleshooting

### Build Errors

**CMake can't find sparkcan:**
```bash
# Make sure sparkcan is installed to system
cd ~/ros2_ws/src/sparkcan/build
sudo make install
sudo ldconfig
```

**Package.xml warnings about tf2:**
- This is a known warning and doesn't affect functionality
- The build should still succeed

### Runtime Errors

**CAN interface not found:**
```bash
# Check if CAN interface exists
ip link show can0

# Manually bring up interface
sudo ip link set can0 type can bitrate 1000000
sudo ip link set up can0
```

**Motors not responding:**
1. Check firmware version (must be 24.0.X)
2. Verify CAN IDs are unique (1-4)
3. Monitor CAN traffic: `candump can0`
4. Check ROS2 node output for errors

**Permission denied on CAN:**
```bash
sudo chmod 666 /dev/can*
```

## Architecture

```
ROS2 Navigation Stack
    ↓ /cmd_vel
SparkFlex Driver Node (C++)
    ↓ SetVelocity()
sparkcan Library
    ↓ CAN frames
Linux SocketCAN
    ↓
CAN HAT
    ↓
SparkFlex Controllers → NEO Motors
```

## Key Files

- **`src/sparkflex_driver_node.cpp`** - Main driver implementation
- **`launch/hardware_bringup.launch.py`** - Hardware launch file
- **`hardware/can/can_setup.sh`** - CAN interface setup script
- **`hardware/can/install_sparkcan.sh`** - SparkCAN installation script
- **`hardware/SPARKCAN_INTEGRATION.md`** - Detailed integration documentation

## Parameters

All parameters are configured in the launch file:

```yaml
wheel_separation: 0.7620  # 30 inches (m)
wheel_radius: 0.1778      # 7 inch wheels (m)
max_rpm: 5700.0           # NEO motor limit
current_limit: 40         # Amps
pid_p: 0.0001            # Proportional gain
pid_ff: 0.000176         # Feed-forward gain
front_left_id: 1          # CAN ID
front_right_id: 2         # CAN ID
rear_left_id: 3           # CAN ID
rear_right_id: 4          # CAN ID
```

## Testing

### Test CAN Communication

```bash
# Monitor CAN bus
candump can0

# Should see periodic heartbeat messages from SparkFlex controllers
```

### Test Motor Control

```bash
# Launch driver
ros2 launch lunabot_one hardware_bringup.launch.py

# In another terminal, send test velocity command
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.1}, angular: {z: 0.0}}" --once
```

### Monitor Odometry

```bash
# View odometry output
ros2 topic echo /odom

# View joint states
ros2 topic echo /joint_states
```

## Important Notes

- **Firmware 24.0.X Required**: sparkcan only works with firmware 24.0.X
- **Heartbeat Critical**: Motors must receive heartbeat every 20ms or they disable
- **CAN Bitrate**: Must be 1 Mbps for SparkFlex
- **Right Side Inverted**: Front-right and rear-right motors are inverted in software

## Next Steps

1. Tune PID parameters for smooth motion
2. Calibrate odometry (wheel separation and radius)
3. Test with joystick/keyboard teleop
4. Integrate with navigation stack

## Support

For issues:
- Check [hardware/SPARKCAN_INTEGRATION.md](hardware/SPARKCAN_INTEGRATION.md)
- Check [HARDWARE_SETUP.md](HARDWARE_SETUP.md)
- sparkcan library: https://github.com/grayson-arendt/sparkcan
