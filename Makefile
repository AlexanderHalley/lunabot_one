# Lunabot One Makefile
# Simplifies common ROS2 launch commands and build operations

.PHONY: help build source clean kill sim sim-nav hardware hardware-nav hardware-test lidar-test ball-tracker joystick minimal-nav full-nav waypoints arena-waypoints

# Default target
help:
	@echo "Lunabot One Commands:"
	@echo ""
	@echo "Build & Setup:"
	@echo "  build         - Build lunabot_one package and source setup"
	@echo "  clean         - Clean build artifacts"
	@echo "  source        - Source install/setup.bash"
	@echo "  kill          - Kill all ROS2, Gazebo, and related processes"
	@echo ""
	@echo "Simulation:"
	@echo "  sim           - Launch Gazebo simulation only"
	@echo "  sim-nav       - Launch simulation with minimal navigation"
	@echo ""
	@echo "Hardware:"
	@echo "  hardware      - Launch hardware bringup"
	@echo "  hardware-nav  - Launch hardware with full navigation"
	@echo "  hardware-test - Launch hardware test mode"
	@echo "  minimal-nav   - Launch minimal navigation (localization only)"
	@echo ""
	@echo "Components:"
	@echo "  lidar-test    - Test lidar merger"
	@echo "  ball-tracker  - Launch ball tracking"
	@echo "  joystick      - Launch joystick control"
	@echo ""
	@echo "Navigation:"
	@echo "  full-nav      - Launch complete nav2 stack (localization + navigation)"
	@echo "  load_map      - Load arena map for visualization"
	@echo "  load_boulder_map - Load arena boulder map for visualization"
	@echo "  slam          - Launch SLAM mapping"
	@echo "  save-map      - Save current SLAM map"
	@echo "  waypoints     - Launch waypoint navigation"
	@echo "  arena-waypoints - Launch arena waypoint navigation"

# Build and setup
build:
	@echo "Building lunabot_one package..."
	cd ~/ros2_ws && colcon build --packages-select lunabot_one && bash -c "source install/setup.bash"

source:
	@echo "Sourcing install/setup.bash..."
	cd ~/ros2_ws && bash -c "source install/setup.bash"

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/lunabot_one install/lunabot_one log/lunabot_one

kill:
	@echo "Killing all ROS2, Gazebo, and related processes..."
	@echo "Stopping ROS2 processes..."
	-pkill -f ros2 2>/dev/null || true
	-pkill -f nav2 2>/dev/null || true
	@echo "Stopping Gazebo processes..."
	-pkill -f gazebo 2>/dev/null || true
	-pkill -f gzserver 2>/dev/null || true
	-pkill -f gzclient 2>/dev/null || true
	-pkill -f gz 2>/dev/null || true
	@echo "Stopping RViz processes..."
	-pkill -f rviz2 2>/dev/null || true
	@echo "Stopping Python waypoint scripts..."
	-pkill -f "python3.*waypoint" 2>/dev/null || true
	-pkill -f "python3.*arena" 2>/dev/null || true
	@echo "Stopping specific navigation processes..."
	-pkill -f planner_server 2>/dev/null || true
	-pkill -f map_server 2>/dev/null || true
	-pkill -f lifecycle_manager 2>/dev/null || true
	-pkill -f controller_server 2>/dev/null || true
	-pkill -f amcl 2>/dev/null || true
	-pkill -f bt_navigator 2>/dev/null || true
	@echo "Waiting for processes to terminate..."
	@sleep 2
	@echo "Force killing any remaining processes..."
	-pkill -9 -f ros2 2>/dev/null || true
	-pkill -9 -f gazebo 2>/dev/null || true
	-pkill -9 -f gz 2>/dev/null || true
	@echo "All processes terminated!"

# Simulation
sim:
	@echo "Launching Gazebo simulation..."
	ros2 launch lunabot_one simulation.launch.py

sim-nav:
	@echo "Launching simulation with minimal navigation..."
	ros2 launch lunabot_one simulation.launch.py & \
	sleep 5 && ros2 launch lunabot_one minimal_navigation_launch.py

# Hardware
hardware:
	@echo "Launching hardware bringup..."
	ros2 launch lunabot_one hardware_bringup.launch.py

hardware-nav:
	@echo "Launching hardware with full navigation..."
	ros2 launch lunabot_one hardware_navigation.launch.py

hardware-test:
	@echo "Launching hardware test mode..."
	ros2 launch lunabot_one hardware_test.launch.py

minimal-nav:
	@echo "Launching minimal navigation (localization only)..."
	ros2 launch lunabot_one minimal_navigation_launch.py use_slam:=false

load_map:
	@echo "Loading arena map..."
	ros2 launch lunabot_one localization_launch.py

load_boulder_map:
	@echo "Loading arena boulder map..."
	ros2 launch lunabot_one localization_launch.py map:=/home/alexanderh/ros2_ws/src/lunabot_one/maps/arena_boulder_map.yaml

# SLAM Mapping
slam:
	@echo "Launching SLAM mapping..."
	ros2 launch lunabot_one slam_launch.py

save-map:
	@echo "Saving map..."
	@read -p "Enter map name (default: new_map): " mapname; \
	mapname=$${mapname:-new_map}; \
	ros2 run nav2_map_server map_saver_cli -f ~/ros2_ws/src/lunabot_one/maps/$$mapname --ros-args -p use_sim_time:=true && \
	echo "Map saved as $$mapname.yaml and $$mapname.pgm"

# Component testing
lidar-test:
	@echo "Testing lidar merger..."
	ros2 launch lunabot_one lidar_merger.launch.py

ball-tracker:
	@echo "Launching ball tracking..."
	ros2 launch lunabot_one ball_tracker.launch.py

joystick:
	@echo "Launching joystick control..."
	ros2 launch lunabot_one joystick.launch.py

# Navigation modes
full-nav:
	@echo "Launching complete nav2 stack (localization + navigation)..."
	ros2 launch lunabot_one full_navigation_launch.py map:=/home/alexanderh/ros2_ws/src/lunabot_one/maps/arena_boulder_map.yaml autoset_pose:=true

waypoints:
	@echo "Launching waypoint navigation..."
	ros2 launch lunabot_one waypoint_navigation.launch.py

arena-waypoints:
	@echo "Launching arena waypoint navigation..."
	ros2 launch lunabot_one arena_waypoints.launch.py