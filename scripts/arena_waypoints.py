#!/usr/bin/env python3

"""
USC Arena Waypoint Navigation

This script contains waypoint coordinates specifically designed for the USC Lunabotics arena.
You can easily modify the coordinates in the ARENA_WAYPOINTS dictionary below.

Arena Layout (6.8m x 5m):
- Starting zone: SW corner (0,0) to (2,2) - Green L-shape boundary  
- Excavation zone: (2,0) to (2.5,5) - Left side of black divider
- Obstacle zone: (2.5,0) to (6.8,5) - Right side with boulders and column
- Construction zone: (3.88,0) to (6.8,1.5) - Black L-shape boundary

Key Obstacles:
- Central column at (3.4, 2.5) - 0.4x0.4m
- Boulder 1 at (3.0, 3.5) - 0.15m radius
- Boulder 2 at (5.5, 4.2) - 0.18m radius  
- Boulder 3 at (6.0, 2.8) - 0.2m radius
- Boulder 4 at (4.5, 4.5) - 0.16m radius
"""

import rclpy
import sys
import os
from waypoint_navigator import WaypointNavigator

# ============================================================================
# EDIT THESE COORDINATES TO CHANGE WAYPOINT BEHAVIOR
# ============================================================================

ARENA_WAYPOINTS = {
    # Basic arena exploration - optimized 4-waypoint path with safe clearance
    'arena_exploration': [
        #Assume you start at 1,1
        (2.0, 4.2, 1.57),    # Go north - above all obstacles, then face east
        (4.75, 3.0, -1.57),  # Move to center area - safe from central column and boulders, then face south
        (5.0, 1.0, 3.14),    # Enter construction zone (goal area), then face west
        (1.0, 1.0, 0.0),     # Return to start, face north
    ],
    
    # Perimeter patrol - follows arena walls
    'arena_perimeter': [
        (0.5, 0.5, 0.0),     # SW corner
        (6.3, 0.5, 1.57),    # SE corner, face north
        (6.3, 4.5, 3.14),    # NE corner, face west
        (0.5, 4.5, -1.57),   # NW corner, face south
        (0.5, 0.5, 0.0),     # Return to SW corner
    ],
    
    # Zone inspection - visit each functional zone
    'zone_inspection': [
        (1.0, 1.0, 0.0),     # Starting zone center
        (1.5, 3.0, 1.57),    # Excavation zone center, face east
        (4.5, 3.5, 3.14),    # Obstacle zone center, face west
        (5.0, 1.0, -1.57),   # Construction zone center, face north
        (1.0, 1.0, 0.0),     # Return to start
    ],
    
    # Obstacle navigation - careful path around obstacles
    'obstacle_navigation': [
        (2.8, 2.0, 0.0),     # Approach central area
        (2.8, 3.2, 1.57),    # Navigate around boulder 1, face east
        (4.2, 3.8, 0.0),     # Move between boulders, face north
        (5.2, 3.8, 1.57),    # Navigate around boulder 2, face east
        (5.8, 3.2, 3.14),    # Navigate around boulder 3, face west
        (4.8, 2.2, -1.57),   # Navigate around column, face south
        (3.6, 2.0, 3.14),    # Clear of column, face west
        (2.8, 2.0, 0.0),     # Return to start position
    ],
    
    # Figure-8 pattern in open areas
    'figure_eight': [
        (1.5, 1.5, 0.0),     # Start position
        (2.0, 2.5, 1.57),    # First curve
        (1.5, 3.5, 3.14),    # Top of first loop
        (1.0, 2.5, -1.57),   # Complete first loop
        (1.5, 1.5, 0.0),     # Center crossing
        (2.0, 0.8, 1.57),    # Second curve
        (1.5, 0.3, 3.14),    # Bottom of second loop (be careful of wall!)
        (1.0, 0.8, -1.57),   # Complete second loop
        (1.5, 1.5, 0.0),     # Return to center
    ],
    
    # Simple test pattern - small movements for testing
    'test_pattern': [
        (1.0, 1.0, 0.0),     # Start
        (1.5, 1.0, 1.57),    # Move east, face north
        (1.5, 1.5, 3.14),    # Move north, face west  
        (1.0, 1.5, -1.57),   # Move west, face south
        (1.0, 1.0, 0.0),     # Return to start
    ],
    
    # Safe path test - avoiding all obstacles
    'safe_path': [
        (1.0, 1.0, 0.0),     # Start in spawn area
        (1.0, 4.0, 0.0),     # Go north - well clear of obstacles
        (3.0, 4.0, 1.57),    # Go east - above boulder 1
        (6.0, 4.0, -1.57),   # Continue to eastern wall
        (6.0, 1.0, 3.14),    # Go south to construction zone  
        (1.0, 1.0, 0.0),     # Return home
    ],
}

# ============================================================================
# END OF EDITABLE COORDINATES
# ============================================================================

def print_available_patterns():
    """Print all available arena waypoint patterns"""
    print("Available arena waypoint patterns:")
    print("=" * 50)
    for name, waypoints in ARENA_WAYPOINTS.items():
        print(f"  {name}: {len(waypoints)} waypoints")
        # Show first few waypoints as preview
        preview = waypoints[:3]
        for i, wp in enumerate(preview):
            if len(wp) == 3:
                print(f"    {i+1}: ({wp[0]:.1f}, {wp[1]:.1f}, {wp[2]:.2f})")
            else:
                print(f"    {i+1}: ({wp[0]:.1f}, {wp[1]:.1f})")
        if len(waypoints) > 3:
            print(f"    ... and {len(waypoints) - 3} more")
        print()

def print_arena_layout():
    """Print arena layout information"""
    print("USC Lunabotics Arena Layout:")
    print("=" * 50)
    print("Arena dimensions: 6.8m x 5.0m")
    print("Coordinate system: SW corner at (0,0)")
    print()
    print("Zones:")
    print("  Starting Zone: (0,0) to (2,2) - Green L-boundary")
    print("  Excavation Zone: (2,0) to (2.5,5) - Left of black line") 
    print("  Obstacle Zone: (2.5,0) to (6.8,5) - Right of black line")
    print("  Construction Zone: (3.88,0) to (6.8,1.5) - Black L-boundary")
    print()
    print("Major Obstacles:")
    print("  Central Column: (3.4, 2.5) - 0.4x0.4m")
    print("  Boulder 1: (3.0, 3.5) - radius 0.15m")
    print("  Boulder 2: (5.5, 4.2) - radius 0.18m")
    print("  Boulder 3: (6.0, 2.8) - radius 0.20m") 
    print("  Boulder 4: (4.5, 4.5) - radius 0.16m")
    print()


def run_pattern(pattern_name):
    """Run a specific arena waypoint pattern"""
    if pattern_name not in ARENA_WAYPOINTS:
        print(f"Error: Pattern '{pattern_name}' not found")
        print()
        print_available_patterns()
        return
        
    waypoints = ARENA_WAYPOINTS[pattern_name]
    print(f"Running arena pattern '{pattern_name}' with {len(waypoints)} waypoints:")
    print("=" * 50)
    for i, wp in enumerate(waypoints):
        if len(wp) == 3:
            print(f"  {i+1}: ({wp[0]:.1f}, {wp[1]:.1f}, {wp[2]:.2f} rad)")
        else:
            print(f"  {i+1}: ({wp[0]:.1f}, {wp[1]:.1f})")
    print()
    print("NOTE: Make sure simulation and navigation are already running!")
    print("      1. ros2 launch lunabot_one simulation.launch.py")
    print("      2. ros2 launch lunabot_one minimal_navigation_launch.py map:=./maps/usc_arena.yaml")
    print("      3. Then run this script")
    print()
    
    rclpy.init()
    navigator = WaypointNavigator(waypoint_pause_duration=2.0)  # 2 seconds pause at each waypoint

    try:
        # Set initial pose to robot spawn area center
        navigator.set_initial_pose(1.0, 1.0, 0.0)
        navigator.get_logger().info("Set initial pose to robot spawn area (1.0, 1.0, 0.0)")

        # Wait a bit for AMCL to initialize
        import time
        time.sleep(3.0)
        
        # Execute waypoints (don't set initial pose again)
        navigator.navigate_waypoints(waypoints, set_initial_pose=False)
        
    except KeyboardInterrupt:
        navigator.get_logger().info('Arena navigation interrupted by user')
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

def main():
    if len(sys.argv) == 1:
        print("USC Arena Waypoint Navigation")
        print("=" * 50)
        print("Usage: python3 arena_waypoints.py <pattern_name>")
        print("       python3 arena_waypoints.py --list")
        print("       python3 arena_waypoints.py --layout")
        print()
        print_available_patterns()
        return
    
    arg = sys.argv[1]
    
    if arg == '--list' or arg == '-l':
        print_available_patterns()
    elif arg == '--layout' or arg == '--map':
        print_arena_layout()
    else:
        run_pattern(arg)

if __name__ == '__main__':
    main()