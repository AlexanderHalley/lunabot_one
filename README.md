Currently getting an rviz error idk why and will look into: (might be my graphic drivers)
[ERROR] [1754542333.222193370] [rviz2]: rviz/glsl120/indexed_8bit_image.vert
rviz/glsl120/indexed_8bit_image.frag
 GLSL link result : 
active samplers with a different type refer to the same texture image unit

# Lunabot One - ROS2 Robot Simulation

## Prerequisites
- ROS2 Jazzy
- Gazebo
- Nav2

## Setup
1. Build the workspace:
   ```bash
   colcon build
   ```

2. Source the workspace:
   ```bash
   source install/setup.bash
   ```

## Launch Instructions

### 1. Start the Simulation
Launch the robot in Gazebo simulation (includes Nintendo Switch controller support):
```bash
ros2 launch lunabot_one simulation.launch.py
```

### 2. Start SLAM (Mapping)
In a new terminal, launch the SLAM toolbox for mapping:
```bash
ros2 launch lunabot_one online_async_launch.py
```

### 3. Start Navigation (Nav2)
In a new terminal, launch the navigation stack:
```bash
ros2 launch lunabot_one navigation_launch.py
```

### 4. Start RViz for Visualization
In a new terminal, launch RViz to visualize the robot and map:
```bash
rviz2
```

## Robot Control Options

### Nintendo Switch Controller (Default)
The controller support is automatically included in the simulation launch.

### Keyboard Teleop (Alternative)
For keyboard control instead of the Nintendo Switch controller:
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/diff_cont/cmd_vel_unstamped
```

## Full Launch Sequence
Open 4-5 terminals and run these commands in order:

1. **Terminal 1 - Simulation:**
   ```bash
   ros2 launch lunabot_one simulation.launch.py
   ```

2. **Terminal 2 - SLAM:**
   ```bash
   ros2 launch lunabot_one online_async_launch.py
   ```

3. **Terminal 3 - Navigation:**
   ```bash
   ros2 launch lunabot_one navigation_launch.py
   ```

4. **Terminal 4 - Visualization:**
   ```bash
   rviz2
   ```

5. **Terminal 5 - Keyboard Control (Optional):**
   ```bash
   ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/diff_cont/cmd_vel_unstamped
   ```