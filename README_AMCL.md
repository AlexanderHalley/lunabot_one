# AMCL Localization Workflow

## Overview
AMCL (Adaptive Monte Carlo Localization) provides more efficient localization on pre-built maps compared to SLAM Toolbox's mapping mode.

## Two-Stage Workflow

### Stage 1: Mapping (Current Setup)
1. Launch SLAM for mapping:
   ```bash
   ros2 launch lunabot_one online_async_launch.py
   ```

2. Drive around to create a good map

3. Save the map:
   ```bash
   ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/lunabot_one/maps/saved_map
   ```

### Stage 2: Localization with AMCL
1. Launch localization mode:
   ```bash
   ros2 launch lunabot_one localization_launch.py
   ```

2. Set initial pose in RViz using "2D Pose Estimate" tool

3. Robot will localize using particle filter

## Benefits of AMCL
- **More efficient**: Lower CPU usage than SLAM
- **Better accuracy**: Dedicated localization algorithm
- **Stable transforms**: Reduces jumping once localized
- **Nav2 integration**: Works seamlessly with navigation stack

## Configuration
- AMCL parameters: `config/params/nav2_params.yaml:1-40`
- Launch file: `launch/localization_launch.py`
- Map location: `maps/saved_map.yaml` (created when you save)

## Switching Between Modes
- **Mapping**: Use `online_async_launch.py` 
- **Localization**: Use `localization_launch.py`
- Both modes use the same robot/Gazebo setup