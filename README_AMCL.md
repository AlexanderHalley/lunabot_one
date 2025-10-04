# AMCL Localization Guide

AMCL (Adaptive Monte Carlo Localization) provides efficient robot localization on pre-built maps using particle filtering.

## Quick Start

### Step 1: Create Map (One-time Setup)
Map the environment first using SLAM:
```bash
make sim
ros2 launch lunabot_one online_async_launch.py
rviz2
# Drive robot around to map entire area
ros2 run nav2_map_server map_saver_cli -f maps/competition_arena
```

### Step 2: Use AMCL for Navigation
Navigate efficiently on the saved map:
```bash
make sim
ros2 launch lunabot_one localization_launch.py map:=maps/competition_arena.yaml
rviz2
# Set initial pose in RViz using "2D Pose Estimate" tool
make arena-waypoints
```

## AMCL vs SLAM Comparison

| Feature | AMCL Localization | SLAM Mapping |
|---------|-------------------|--------------|
| **Use case** | Known environments | Unknown environments |
| **CPU usage** | Low (~15% less) | Higher |
| **Accuracy** | Higher (dedicated algorithm) | Good |
| **Setup time** | Requires pre-built map | Works immediately |
| **Competition strategy** | Recommended for runs | Used for initial scouting |
| **Transform stability** | Very stable | Can jump during loop closure |
| **Memory usage** | Lower | Higher (maintains map) |

## When to Use Each Method

### Use AMCL Localization When:
- Environment is previously mapped
- Running competition missions
- Need maximum navigation performance
- Want stable, accurate localization
- CPU resources are limited

### Use SLAM Mapping When:
- Exploring unknown environments
- Creating new maps
- Environment has changed significantly
- No existing map available

## AMCL Configuration

### Key Parameters (nav2_params.yaml)
```yaml
amcl:
  alpha1: 0.2          # Rotation noise from rotation
  alpha2: 0.2          # Rotation noise from translation
  alpha3: 0.2          # Translation noise from translation
  alpha4: 0.2          # Translation noise from rotation
  min_particles: 500   # Minimum particle count
  max_particles: 2000  # Maximum particle count
  initial_pose:        # Set if known starting position
    x: 0.0
    y: 0.0
    yaw: 0.0
```

### Performance Tuning
- **More particles**: Better accuracy, higher CPU usage
- **Fewer particles**: Faster processing, may lose tracking
- **Noise parameters**: Tune based on wheel slip and IMU accuracy
- **Update frequencies**: Balance between accuracy and performance

## Troubleshooting

### Poor Localization Performance
**Increase particle count:**
```yaml
# In nav2_params.yaml
min_particles: 1000
max_particles: 5000
```

**Check initial pose accuracy:**
```bash
ros2 topic echo /amcl_pose --once
# Should match robot's actual position in RViz
```

### Initial Pose Problems
**Competition Arena Coordinate System:**
- **Origin (0,0)**: Bottom-left corner of arena
- **Robot spawn**: (1,1) - default starting position
- **Orientation**: 0 radians = facing positive X (right)

**Set pose manually in RViz:**
1. Click "2D Pose Estimate" tool
2. Click robot's actual position on map
3. Drag to set orientation
4. Check `/amcl_pose` topic confirms position

**Set pose programmatically (robot at spawn):**
```bash
ros2 topic pub /initialpose geometry_msgs/PoseWithCovarianceStamped '{
  header: {frame_id: "map"},
  pose: {
    pose: {
      position: {x: 1.0, y: 1.0, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    }
  }
}'
```

**Set pose at origin corner:**
```bash
ros2 topic pub /initialpose geometry_msgs/PoseWithCovarianceStamped '{
  header: {frame_id: "map"},
  pose: {
    pose: {
      position: {x: 0.0, y: 0.0, z: 0.0},
      orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
    }
  }
}'
```

### Transform Errors
**Check transform chain:**
```bash
ros2 run tf2_tools view_frames
# Should show: map -> odom -> base_link
```

**Verify map server:**
```bash
ros2 topic echo /map --once
# Should show map data
```

## Advanced Features

### IMU Integration
AMCL can use IMU data for improved orientation tracking:
```yaml
# In nav2_params.yaml
use_imu: true
imu_topic: "/imu/data"
```

### Localization Monitoring
**Check particle spread:**
```bash
ros2 topic echo /particlecloud
# Tight cluster = good localization
# Spread particles = poor localization
```

**Monitor localization quality:**
```bash
ros2 topic echo /amcl/parameter_updates
# Shows real-time algorithm adjustments
```

## Competition Workflow

### Pre-Competition Mapping
```bash
# Scout the arena and create high-quality map
make sim  # Or make hardware for real robot
ros2 launch lunabot_one online_async_launch.py
# Drive comprehensive mapping route
ros2 run nav2_map_server map_saver_cli -f maps/competition_final
```

### Competition Run
```bash
# Fast startup with known map
make sim  # Or make hardware
ros2 launch lunabot_one localization_launch.py map:=maps/competition_final.yaml
# Set initial pose quickly
make arena-waypoints pattern=competition_mission
```

## Debug Commands

```bash
# Check AMCL status
ros2 node info /amcl

# Monitor particle cloud
ros2 topic echo /particlecloud

# View current pose estimate
ros2 topic echo /amcl_pose

# Check map service
ros2 service call /map_server/load_map nav2_msgs/LoadMap

# Reset localization
ros2 service call /reinitialize_global_localization std_srvs/Empty
```

## File Locations

- **AMCL parameters**: `config/params/nav2_params.yaml` (lines 1-40)
- **Launch file**: `launch/localization_launch.py`
- **Map files**: `maps/` directory (.yaml + .pgm files)
- **Documentation**: See [NAVIGATION_README.md](NAVIGATION_README.md) for full workflows