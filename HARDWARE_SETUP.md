# Lunabot One Hardware Setup Guide

This guide covers setting up the physical robot with Raspberry Pi 5, CAN HAT, and 4 SparkFlex motor controllers.

## Hardware Requirements

### Core Components
- **Raspberry Pi 5** (4GB+ RAM recommended)
- **CAN HAT** (e.g., Waveshare RS485/CAN HAT, Seeed Studio 2-Channel CAN-BUS HAT)
- **4x SparkFlex Motor Controllers**
- **4x NEO Brushless Motors** (or compatible BLDC motors)
- **Power supply** (suitable for your motors + Pi)
- **Lidar sensor** (e.g., LDLidar LD19, Slamtec RPLidar)
- **MicroSD card** (64GB+ recommended)

### Wiring Setup
```
Raspberry Pi 5
    ↓ (40-pin GPIO)
CAN HAT
    ↓ (CAN H/L)
CAN Bus (daisy chain)
    ├── SparkFlex #1 (CAN ID: 1) → Front Left Motor
    ├── SparkFlex #2 (CAN ID: 2) → Front Right Motor
    ├── SparkFlex #3 (CAN ID: 3) → Rear Left Motor
    └── SparkFlex #4 (CAN ID: 4) → Rear Right Motor
```

## Software Prerequisites

### 1. Raspberry Pi OS Setup
```bash
# Install ROS2 Jazzy (follow official ROS2 installation guide)
# Install additional packages
sudo apt update
sudo apt install -y can-utils python3-can

# Enable CAN interface in /boot/config.txt
echo "dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25" | sudo tee -a /boot/config.txt
echo "dtoverlay=spi1-3cs" | sudo tee -a /boot/config.txt

# Reboot required after config changes
sudo reboot
```

### 2. SparkCAN Library Installation
```bash
# Install sparkcan library (Linux CAN interface for SparkFlex)
sudo add-apt-repository ppa:graysonarendt/sparkcan
sudo apt update
sudo apt install sparkcan

# Build your ROS2 workspace
cd ~/ros2_ws
colcon build --packages-select lunabot_one
source install/setup.bash
```

## SparkFlex Configuration

### 1. Individual SparkFlex Setup
For each SparkFlex controller, configure via USB before CAN deployment using REV Hardware Client:

**Using REV Hardware Client:**
1. Download and install [REV Hardware Client](https://docs.revrobotics.com/rev-hardware-client/)
2. Connect each SparkFlex via USB
3. Configure each controller:
   - **Set CAN ID**: 1, 2, 3, or 4 (front left, front right, rear left, rear right)
   - **Motor Type**: Set to Brushless (for NEO motors)
   - **Idle Mode**: Brake mode recommended
   - **Current Limit**: 40A (adjust based on your motors)
   - **Firmware**: Ensure firmware 24.0.X is installed (sparkcan requires 24.0.X, not 25.0.X)

4. Burn settings to flash and test motor direction
5. Repeat for all four SparkFlex controllers

**Important Notes:**
- sparkcan library only works with firmware 24.0.X
- Use REV Hardware Client to downgrade if you have 25.0.X
- Ensure each controller has a unique CAN ID (1-4)

### 2. Verify CAN Communication
```bash
# Setup CAN interface
sudo bash ~/ros2_ws/src/lunabot_one/hardware/can/can_setup.sh

# Monitor CAN traffic (should see periodic heartbeat messages)
candump can0

# You should see messages from SparkFlex controllers with IDs 1-4
# SparkFlex automatically sends periodic status frames
```

## Launch Sequence

### 1. Hardware Bringup Only
Test basic robot control without navigation:
```bash
ros2 launch lunabot_one hardware_bringup.launch.py
```

### 2. Hardware Testing 
Interactive testing with CAN monitoring:
```bash
ros2 launch lunabot_one hardware_test.launch.py can_monitor:=true
```

### 3. Full Navigation System
Complete autonomous navigation:
```bash
ros2 launch lunabot_one hardware_navigation.launch.py map:=/path/to/your/map.yaml
```

## Configuration Files

### Key Parameters to Customize
1. **`launch/hardware_bringup.launch.py`** - Motor CAN IDs and robot dimensions
2. **`config/params/hardware_nav2_params.yaml`** - Navigation parameters for hardware

### Robot Dimensions
Update these parameters in the launch file or via ROS2 parameters:
```yaml
wheel_separation: 0.7620  # Distance between left/right wheels (m) - 30 inches
wheel_radius: 0.1778      # Wheel radius (m) - 7 inch wheels
max_rpm: 5700.0           # Maximum motor RPM (NEO motor limit)
current_limit: 40         # Current limit in amps
```

## Troubleshooting

### CAN Interface Issues
```bash
# Check CAN interface status
ip link show can0

# Manual CAN setup if script fails
sudo ip link set can0 type can bitrate 1000000
sudo ip link set up can0

# Reset CAN interface
sudo ip link set down can0
sudo ip link set up can0
```

### SparkFlex Communication Issues
```bash
# Check SparkFlex heartbeat (should see periodic messages from IDs 1-4)
candump can0

# Verify CAN IDs are correct
# Each SparkFlex should be sending periodic status frames
```

### Motor Not Moving
1. **Check firmware version** - Must be 24.0.X (not 25.0.X)
2. **Verify CAN IDs** - Each controller must have unique ID (1-4)
3. **Check current limits** - Ensure limits are appropriate for NEO motors (40A recommended)
4. **Verify motor type** - Must be set to Brushless in REV Hardware Client
5. **Monitor error messages** - Check ROS2 node output for sparkcan errors

### Navigation Issues
1. **Odometry drift** - Tune wheel separation multiplier in controller config
2. **Localization problems** - Ensure lidar is properly configured and mounted
3. **Path planning failures** - Check costmap parameters for hardware-specific tuning

## Safety Considerations

**Important Safety Notes:**
- Always have an emergency stop mechanism
- Test at low speeds initially (max_velocity: 0.5 m/s)
- Ensure adequate power supply for all motors
- Monitor motor temperatures during operation
- Keep clear of robot during initial testing

## Performance Tuning

### Motor Control
- Adjust current limits based on motor specifications (40A for NEO motors)
- Tune PID parameters for smooth motion (P and FF gains in driver node parameters)
- Configure max RPM based on your motors (5700 RPM for NEO motors)

### Navigation
- Reduce maximum velocities for safety
- Adjust costmap resolution for computational performance
- Tune AMCL parameters for better localization

## Development Workflow

1. **Hardware Testing**: Use `hardware_test.launch.py`
2. **Manual Control**: Test with keyboard/joystick teleop
3. **Mapping**: Create maps using SLAM
4. **Navigation**: Test autonomous goal navigation
5. **Parameter Tuning**: Adjust performance parameters

For detailed navigation setup, see [NAVIGATION_README.md](NAVIGATION_README.md)