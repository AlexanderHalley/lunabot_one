# Lunabot One Makefile
# Simplifies common ROS2 launch commands and build operations

.PHONY: help build source clean sim sim-nav hardware hardware-nav hardware-test lidar-test ball-tracker joystick minimal-nav waypoints arena-waypoints

# Default target
help:
	@echo "Lunabot One Commands:"
	@echo ""
	@echo "Build & Setup:"
	@echo "  build         - Build lunabot_one package and source setup"
	@echo "  clean         - Clean build artifacts"
	@echo "  source        - Source install/setup.bash"
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

# Simulation
sim:
	@echo "Launching Gazebo simulation..."
	ros2 launch lunabot_one simulation.launch.py

sim-nav:
	@echo "Launching simulation with minimal navigation..."
	ros2 launch lunabot_one simulation.launch.py & \
	sleep 5 && ros2 launch lunabot_one minimal_navigation_launch.py map:=/home/alexanderh/ros2_ws/src/lunabot_one/maps/arena_map.yaml

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
waypoints:
	@echo "Launching waypoint navigation..."
	ros2 launch lunabot_one waypoint_navigation.launch.py

arena-waypoints:
	@echo "Launching arena waypoint navigation..."
	ros2 launch lunabot_one arena_waypoints.launch.py