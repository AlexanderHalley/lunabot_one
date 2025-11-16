# OAK-D S2 Camera Integration & Troubleshooting Guide

This guide covers the setup, testing, and troubleshooting of the Intel RealSense OAK-D S2 camera integration for Lunabot One.

## Table of Contents
1. [Hardware Requirements](#hardware-requirements)
2. [Installation & Setup](#installation--setup)
3. [Testing the Camera](#testing-the-camera)
4. [Troubleshooting](#troubleshooting)
5. [Common Issues & Solutions](#common-issues--solutions)
6. [Performance Notes](#performance-notes)
7. [Integration with Full Hardware Stack](#integration-with-full-hardware-stack)

---

## Hardware Requirements

### Physical Setup
- **OAK-D S2 Camera**: Intel RealSense OAK-D Stereo camera
- **USB 3.1 Connection**: Camera requires USB 3.1 with sufficient power
- **Raspberry Pi 5** (or compatible system): Host computer
- **USB Cable**: High-quality USB 3.1 Type-C cable (included with camera)

### Recommended Specifications
- **Min USB Power**: 500mA (800mA recommended for optimal performance)
- **Camera Mounting**: Front of robot, elevation ~15cm above chassis
- **Field of View**: ~127° horizontal for stereo depth
- **Operating Temperature**: 0°C to 40°C

### Raspberry Pi 5 Considerations
- **USB Port**: Use USB 3.0+ port (ports labeled blue)
- **Power Supply**: Ensure 5V/5A PSU for reliable USB power
- **Thermal Management**: Camera + ROS2 may cause CPU heat; consider active cooling

---

## Installation & Setup

### Step 1: Install depthai-ros Package

```bash
# Option A: Binary installation (Recommended for RPi5)
sudo apt update
sudo apt install ros-humble-depthai-ros

# Option B: Build from source (if binary not available)
cd ~/ros2_ws/src
git clone --branch humble https://github.com/luxonis/depthai-ros.git
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select depthai_ros
```

### Step 2: Verify Installation

```bash
# Check if depthai_ros package is available
ros2 pkg list | grep depthai

# Check if OAK-D is recognized
lsusb | grep OAK
# Expected output: Bus 001 Device XXX: ID 03e7:2485 Intel Movidius MyriadX
```

### Step 3: USB Permissions (If needed)

```bash
# Add user to dialout group for USB access
sudo usermod -aG dialout $USER
sudo usermod -aG video $USER

# Log out and back in for changes to take effect
```

### Step 4: Build lunabot_one Package

```bash
cd ~/lunabotics_ws
colcon build --packages-select lunabot_one
source install/setup.bash
```

---

## Testing the Camera

### Quick Start: Standalone Camera Test

This is the simplest way to test the camera without the full robot stack.

```bash
# Basic RGB camera test with RViz visualization
ros2 launch lunabot_one test_oak_d_camera.launch.py

# Test with depth image visualization
ros2 launch lunabot_one test_oak_d_camera.launch.py show_depth:=true

# Test with point cloud (requires more CPU)
ros2 launch lunabot_one test_oak_d_camera.launch.py show_pointcloud:=true

# Disable RViz (headless operation)
ros2 launch lunabot_one test_oak_d_camera.launch.py rviz:=false

# Enable debug logging
ros2 launch lunabot_one test_oak_d_camera.launch.py log_level:=DEBUG
```

### What the Launch File Does

1. **Starts OAK-D Driver** (`depthai_ros` RGB-Stereo node)
   - Publishes RGB images to `/camera/color/image_raw`
   - Publishes depth images to `/camera/stereo/depth`
   - Publishes point cloud to `/camera/stereo/points`
   - Publishes camera calibration to `/camera/*/camera_info`

2. **Starts Robot State Publisher**
   - Publishes camera frame transforms (`camera_link`, `camera_rgb_optical_frame`, `camera_stereo_optical_frame`)

3. **Starts RViz2**
   - Auto-generated minimal config for camera visualization
   - Displays RGB image, depth image, and point cloud
   - Saves config to `/tmp/oak_d_test.rviz`

### Verifying Camera Output

```bash
# In another terminal, check if topics are being published
ros2 topic list | grep camera
# Should see topics like:
# /camera/color/image_raw
# /camera/color/camera_info
# /camera/stereo/depth
# /camera/stereo/camera_info
# /camera/stereo/points

# Check frame rate
ros2 topic hz /camera/color/image_raw
# Should show ~30 Hz (configurable)

# View a single frame from RGB camera
ros2 run image_tools image_view --ros-args -r image:=/camera/color/image_raw

# View depth image
ros2 run image_tools image_view --ros-args -r image:=/camera/stereo/depth
```

---

## Troubleshooting

### Initial Checks

Before diagnosing specific issues, run these checks:

1. **USB Connection**
   ```bash
   lsusb | grep -i oak
   ```
   Should show one OAK-D device

2. **ROS2 Installation**
   ```bash
   ros2 pkg list | grep depthai
   ```
   Should list `depthai_ros` package

3. **Camera Recognition**
   ```bash
   ros2 run depthai_ros list_cameras
   # Should show OAK-D S2 device info
   ```

4. **File Permissions**
   ```bash
   ls -la /dev/bus/usb/*/
   # User should have read/write permissions
   ```

### Diagnostic Workflow

#### 1. Check Camera Hardware
```bash
# Test if camera is accessible
ros2 run depthai_ros rgb_stereo_node --ros-args --log-level DEBUG 2>&1 | head -20
```

Expected output should include:
- `[OAK-D S2]` or device name
- `Connected to device`
- Firmware version information

#### 2. Monitor Node Output
```bash
# Run with enhanced logging
ros2 launch lunabot_one test_oak_d_camera.launch.py log_level:=DEBUG camera_enabled:=true rviz:=false
```

#### 3. Check Topic Publishing
```bash
# Verify topics exist
ros2 topic list | grep camera

# Monitor topic messages
ros2 topic info /camera/color/image_raw

# Check message rate
ros2 topic hz /camera/color/image_raw
```

#### 4. Inspect Frame Transforms
```bash
# Check if camera frames are being published
ros2 run tf2_tools view_frames.py
# Opens a PDF with transform tree

# List all available frames
ros2 run tf2_ros tf2_echo camera_link camera_rgb_optical_frame
```

---

## Common Issues & Solutions

### Issue 1: "Device not found" or "Camera not detected"

**Symptoms:**
- Error: `[ERROR] Device not found`
- Error: `Connection failed`
- No output after launching

**Causes & Solutions:**

1. **USB Connection Issues**
   ```bash
   # Check USB port
   lsusb

   # Try different USB 3.1 port (usually blue ports)
   # Avoid USB hubs if possible
   ```

2. **USB Permissions**
   ```bash
   # Check device ownership
   ls -la /dev/bus/usb/*/

   # Grant permissions
   sudo chown $USER:$USER /dev/bus/usb/*/*
   # OR add user to group (requires logout/login)
   sudo usermod -aG video $USER
   sudo usermod -aG dialout $USER
   ```

3. **USB Power Insufficient**
   - Check if Raspberry Pi power supply is adequate (5V/5A recommended)
   - Try connecting camera to powered USB hub
   - Reduce CPU load on other processes

4. **Firmware Issue**
   ```bash
   # Update OAK-D firmware
   ros2 run depthai_ros update_device_firmware -d 16
   ```

**Quick Fix:**
```bash
# Restart USB subsystem
sudo systemctl restart usbhotplug
# OR unplug/replug camera and retry
```

---

### Issue 2: "Permission denied" when accessing camera

**Symptoms:**
- Error: `Permission denied (os error 13)`
- Error: `Cannot access device`

**Solution:**
```bash
# Add current user to required groups
sudo usermod -aG dialout $USER
sudo usermod -aG video $USER
sudo usermod -aG render $USER

# Log out and log back in
# OR use newgrp to activate group immediately
newgrp video
newgrp render

# Verify
groups $USER
# Should include: dialout, video, render, etc.
```

---

### Issue 3: "No image data" or blank RViz display

**Symptoms:**
- RViz shows no images
- Topics exist but no data flowing
- `/camera/color/image_raw` has no subscribers

**Diagnosis & Solution:**

1. **Check if driver is running**
   ```bash
   ros2 node list | grep oak
   # Should show camera driver node
   ```

2. **Verify topic publishing**
   ```bash
   ros2 topic echo /camera/color/image_raw --once
   # Should output an image message
   ```

3. **Check camera configuration**
   ```bash
   # Ensure config file is readable
   cat /home/lunapi/lunabotics_ws/src/lunabot_one/config/camera/oak_d_s2.yaml
   ```

4. **Restart driver with debug output**
   ```bash
   ros2 launch lunabot_one test_oak_d_camera.launch.py log_level:=DEBUG

   # Look for lines like:
   # [INFO] ... Camera initialized
   # [INFO] ... Publishing to /camera/color/image_raw
   ```

---

### Issue 4: Poor depth image quality or "all black" depth

**Symptoms:**
- Depth image appears completely black
- Depth values all zeros
- Point cloud is empty

**Causes & Solutions:**

1. **Depth Detection Range**
   - OAK-D S2 stereo depth works best at 40cm - 5m distance
   - If object is too close or too far, no depth detected
   - Solution: Move camera closer to objects (40cm-2m range optimal)

2. **Lighting Conditions**
   - Stereo depth requires ambient light for texture matching
   - Dark environments produce poor depth
   - Solution: Increase ambient lighting or use IR illumination mode

3. **Surface Texture**
   - Featureless, reflective, or transparent surfaces cause issues
   - Solution: Add texture/pattern or use objects with natural features

4. **Confidence Threshold**
   - Default threshold may be too strict
   - Edit `/config/camera/oak_d_s2.yaml`:
   ```yaml
   stereo_depth:
     confidence_threshold: 200  # Lower = more lenient (0-255)
   ```

5. **Check Depth Alignment**
   ```bash
   # Verify depth is aligned to RGB
   ros2 param get /camera/oak_d_driver stereo_depth.align_depth
   # Should return: rgb
   ```

---

### Issue 5: High CPU usage or frame drops

**Symptoms:**
- ROS2 nodes running slow
- Low frame rate (< 15 fps)
- System becomes unresponsive
- Thermal throttling on Raspberry Pi

**Solutions:**

1. **Reduce Resolution**
   ```yaml
   # In oak_d_s2.yaml:
   rgb:
     resolution: "720P"  # Changed from 1080P
   ```

2. **Reduce Frame Rate**
   ```yaml
   rgb:
     fps: 15  # Changed from 30
   stereo_depth:
     fps: 15
   ```

3. **Disable Point Cloud Generation**
   - Point cloud processing is CPU-intensive
   - Use `show_pointcloud:=false` in launch command
   - Or disable in config:
   ```yaml
   spatial_detection:
     enabled: false
   ```

4. **Use Nodelet for Efficiency**
   ```yaml
   use_nodelet: true  # Already enabled in our config
   ```

5. **Monitor System Resources**
   ```bash
   htop  # Monitor CPU and memory usage
   vcgencmd measure_temp  # Check Raspberry Pi temperature
   # If temp > 80°C, add heat sink or increase cooling
   ```

---

### Issue 6: RViz showing "Fixed Frame" error

**Symptoms:**
- RViz: "No transform from camera_link to camera_rgb_optical_frame"
- RViz: "Frame not found"

**Cause:** Robot state publisher not running or URDF not loading

**Solution:**
```bash
# Verify robot state publisher is running
ros2 node list | grep robot_state_publisher

# Check if camera frames are in TF tree
ros2 run tf2_tools view_frames.py
# Open the generated PDF

# If frames missing, check URDF
ros2 param get /robot_state_publisher robot_description
```

---

### Issue 7: "depthai_ros package not found"

**Symptoms:**
- Error: `[ERROR] Could not find requested package depthai_ros`
- Package lookup failed

**Solution:**

1. **Install from repositories**
   ```bash
   sudo apt update
   sudo apt install ros-humble-depthai-ros
   ```

2. **Verify installation**
   ```bash
   dpkg -l | grep depthai
   ```

3. **Source setup.bash**
   ```bash
   source /opt/ros/humble/setup.bash
   ros2 pkg list | grep depthai
   ```

4. **If still not found, build from source**
   ```bash
   cd ~/ros2_ws/src
   git clone --branch humble https://github.com/luxonis/depthai-ros.git
   cd ~/ros2_ws
   colcon build --packages-select depthai_ros
   source install/setup.bash
   ```

---

## Performance Notes

### Raspberry Pi 5 Performance

The Raspberry Pi 5 can handle OAK-D S2 with the following configuration:

| Mode | Resolution | FPS | CPU Load | Notes |
|------|------------|-----|----------|-------|
| RGB Only | 1080P | 30 | ~40% | Baseline |
| RGB + Depth | 1080P | 30 | ~70% | Moderate load |
| RGB + Depth + PC | 1080P | 30 | ~95% | Near limit |
| RGB + Depth | 720P | 30 | ~55% | Recommended |
| RGB + Depth | 720P | 15 | ~30% | Low power mode |

**Recommendation:** Use 720P @ 30 FPS for balanced performance.

### Optimization Tips

1. **Disable Unused Outputs**
   - Disable point cloud if not needed
   - Disable depth if only RGB needed
   - Disable IR projector if not stereo

2. **Reduce Update Rates**
   - Lower TF publication rate if not needed
   - Adjust diagnostic frequency

3. **Use Nodelet**
   - Already configured in oak_d_s2.yaml
   - Reduces inter-process communication overhead

4. **Thermal Management**
   - Ensure adequate cooling
   - Monitor temperature with `vcgencmd measure_temp`
   - Add heatsink if temp > 75°C

---

## Integration with Full Hardware Stack

Once camera is working standalone, integrate with full robot:

### Step 1: Update hardware_bringup.launch.py

Add camera node launch:
```python
# In hardware_bringup.launch.py
camera_node = IncludeLaunchDescription(
    PythonLaunchDescriptionSource(
        PathJoinSubstitution([
            FindPackageShare('lunabot_one'),
            'launch',
            'oak_d_camera.launch.py'
        ])
    ),
    condition=IfCondition(LaunchConfiguration('camera'))
)
```

### Step 2: Add to navigation stack

Update navigation launch to include camera topics in bridge configuration.

### Step 3: Update ball_tracker integration

Camera topics are already configured for ball_tracker:
- RGB: `/camera/color/image_raw`
- Depth: `/camera/stereo/depth`
- Point Cloud: `/camera/stereo/points`

No additional configuration needed.

### Step 4: Test full integration

```bash
# Start full hardware stack
ros2 launch lunabot_one hardware_bringup.launch.py camera:=true

# In another terminal, verify all topics
ros2 topic list | grep -E "(camera|scan|odom|cmd_vel)"
```

---

## Useful Commands Reference

```bash
# List available nodes and topics
ros2 node list
ros2 topic list

# View camera information
ros2 run depthai_ros list_cameras
ros2 run depthai_ros stereo_info_viewer

# Record camera data
ros2 bag record /camera/color/image_raw /camera/stereo/depth

# View TF tree
ros2 run tf2_tools view_frames.py

# Monitor specific topic
ros2 topic echo /camera/color/image_raw --once
ros2 topic hz /camera/color/image_raw

# Kill stuck camera process
pkill -f oak_d_driver
# OR
ros2 node kill /camera/oak_d_driver
```

---

## Support & Resources

- **depthai-ros Documentation**: https://github.com/luxonis/depthai-ros
- **OAK-D Hardware Specs**: https://github.com/luxonis/oak-d-bringup
- **ROS2 Camera Documentation**: https://wiki.ros.org/camera1394
- **Intel RealSense Support**: https://github.com/IntelRealSense/librealsense/issues

---

## Notes for Development

- Configuration file: `config/camera/oak_d_s2.yaml`
- Launch file: `launch/test_oak_d_camera.launch.py`
- URDF definition: `description/oak_d_s2.xacro`
- Hardware URDF: `urdf/lunabot_hardware.urdf.xacro`

All files support easy customization for different mounting positions or configurations.
