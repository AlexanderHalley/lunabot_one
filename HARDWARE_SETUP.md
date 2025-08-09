# Lunabot One Hardware Setup Guide

This guide covers setting up the physical robot with Raspberry Pi 5, CAN HAT, and 4 ODrive S1 motor controllers.

## Hardware Requirements

### Core Components
- **Raspberry Pi 5** (4GB+ RAM recommended)
- **CAN HAT** (e.g., Waveshare RS485/CAN HAT, Seeed Studio 2-Channel CAN-BUS HAT)
- **4x ODrive S1 Motor Controllers**
- **4x BLDC Motors** (compatible with ODrive S1)
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
    ├── ODrive S1 #1 (CAN ID: 0x001) → Front Left Motor
    ├── ODrive S1 #2 (CAN ID: 0x002) → Front Right Motor  
    ├── ODrive S1 #3 (CAN ID: 0x003) → Rear Left Motor
    └── ODrive S1 #4 (CAN ID: 0x004) → Rear Right Motor
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

### 2. ODrive ROS2 Package Installation
```bash
# Install ODrive ROS2 control package (assuming it exists)
# Note: This may need to be built from source depending on availability
cd ~/ros2_ws/src
git clone https://github.com/odriverobotics/odrive_ros2_control.git  # Hypothetical repo
cd ~/ros2_ws
colcon build --packages-select odrive_ros2_control
source install/setup.bash
```

## ODrive Configuration

### 1. Individual ODrive Setup
For each ODrive S1, configure via USB before CAN deployment:

```bash
# Install ODrive Python tools
pip install odrive

# Connect each ODrive via USB and configure:
odrivetool

# In odrivetool, configure each ODrive:
odrv0.config.enable_brake_resistor = False  # Unless you have brake resistor
odrv0.config.brake_resistance = 2.0

# Configure CAN
odrv0.config.can.node_id = 1  # Set to 1, 2, 3, or 4 respectively
odrv0.config.can.baudrate = 1000000  # 1 Mbps

# Motor configuration (adjust for your specific motor)
odrv0.axis0.motor.config.current_limit = 10.0
odrv0.axis0.motor.config.calibration_current = 10.0
odrv0.axis0.motor.config.resistance_calib_max_voltage = 2.0
odrv0.axis0.motor.config.pole_pairs = 7  # Adjust for your motor
odrv0.axis0.motor.config.torque_constant = 0.04

# Encoder configuration (ODrive S1 has built-in encoder)
odrv0.axis0.encoder.config.cpr = 8192

# Save configuration and reboot ODrive
odrv0.save_configuration()
odrv0.reboot()
```

### 2. Verify CAN Communication
```bash
# Setup CAN interface
sudo bash ~/ros2_ws/src/lunabot_one/hardware/can/can_setup.sh

# Monitor CAN traffic
candump can0

# Send test message to ODrive (should see response)
cansend can0 001#0100  # Request heartbeat from ODrive ID 1
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

### Key Files to Customize
1. **`hardware/can/odrive_can_ids.yaml`** - CAN ID mapping and robot dimensions
2. **`hardware/odrive/motor_params.yaml`** - Motor-specific parameters
3. **`config/control/hardware/hardware_controllers.yaml`** - ROS2 control configuration
4. **`config/params/hardware_nav2_params.yaml`** - Navigation parameters for hardware

### Robot Dimensions
Update these values in `hardware/can/odrive_can_ids.yaml`:
```yaml
diff_drive:
  wheel_separation: 0.782  # Distance between left/right wheels (m)
  wheel_radius: 0.165      # Wheel radius (m)
  max_velocity: 2.0        # Maximum linear velocity (m/s)
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

### ODrive Communication Issues
```bash
# Check ODrive heartbeat (should see periodic messages)
candump can0 | grep "heartbeat"

# Send specific ODrive commands
cansend can0 001#0700  # Set axis state to IDLE
cansend can0 001#0800  # Set axis state to CLOSED_LOOP_CONTROL
```

### Motor Not Moving
1. **Check motor calibration** - ODrives need motor calibration on first use
2. **Verify current limits** - May be set too low for your motors
3. **Check enable state** - Motors must be enabled (closed-loop control)
4. **Monitor error messages** - Use `candump can0` to see error codes

### Navigation Issues
1. **Odometry drift** - Tune wheel separation multiplier in controller config
2. **Localization problems** - Ensure lidar is properly configured and mounted
3. **Path planning failures** - Check costmap parameters for hardware-specific tuning

## Safety Considerations

⚠️ **Important Safety Notes:**
- Always have an emergency stop mechanism
- Test at low speeds initially (max_velocity: 0.5 m/s)
- Ensure adequate power supply for all motors
- Monitor motor temperatures during operation
- Keep clear of robot during initial testing

## Performance Tuning

### Motor Control
- Adjust current limits based on motor specifications
- Tune PID parameters for smooth motion
- Configure acceleration/deceleration limits

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