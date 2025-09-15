#!/usr/bin/env python3

"""
Example waypoint patterns for autonomous navigation

This file contains predefined waypoint sequences that can be used
for testing and demonstrating the waypoint navigation system.
"""

import rclpy
from waypoint_navigator import WaypointNavigator

# Predefined waypoint patterns
WAYPOINT_PATTERNS = {
    'square': [
        (2.0, 0.0),    # Go forward
        (2.0, 2.0),    # Turn right  
        (0.0, 2.0),    # Go back
        (0.0, 0.0),    # Return to start
    ],
    
    'rectangle': [
        (3.0, 0.0),    # Go forward (longer)
        (3.0, 1.5),    # Turn right
        (0.0, 1.5),    # Go back  
        (0.0, 0.0),    # Return to start
    ],
    
    'triangle': [
        (2.0, 0.0),      # Go forward
        (1.0, 1.73),     # Go to apex (equilateral triangle)
        (0.0, 0.0),      # Return to start
    ],
    
    'figure_eight': [
        (1.0, 0.0),      # Move forward
        (2.0, 1.0),      # First curve
        (1.0, 2.0),      # Top of first loop
        (0.0, 1.0),      # Complete first loop
        (1.0, 0.0),      # Center crossing
        (2.0, -1.0),     # Second curve  
        (1.0, -2.0),     # Bottom of second loop
        (0.0, -1.0),     # Complete second loop
        (0.0, 0.0),      # Return to start
    ],
    
    'exploration': [
        (2.0, 0.0),      # Explore forward
        (2.0, 1.0),      # Explore right
        (1.0, 2.0),      # Explore up-left
        (-1.0, 1.5),     # Explore left
        (-1.0, -1.0),    # Explore down-left  
        (1.0, -1.5),     # Explore down-right
        (0.0, 0.0),      # Return home
    ],
    
    # Patterns with orientations (x, y, yaw)
    'oriented_square': [
        (2.0, 0.0, 1.57),    # Forward, face right
        (2.0, 2.0, 3.14),    # Right, face back
        (0.0, 2.0, -1.57),   # Back, face left  
        (0.0, 0.0, 0.0),     # Left, face forward
    ],
    
    'inspection_points': [
        (1.0, 1.0, 0.0),     # Point 1, face forward
        (1.0, 1.0, 1.57),    # Same point, face right
        (1.0, 1.0, 3.14),    # Same point, face back
        (1.0, 1.0, -1.57),   # Same point, face left
        (1.0, 1.0, 0.0),     # Same point, face forward again
        (0.0, 0.0, 0.0),     # Return home
    ]
}

def print_available_patterns():
    """Print all available waypoint patterns"""
    print("Available waypoint patterns:")
    for name, waypoints in WAYPOINT_PATTERNS.items():
        print(f"  {name}: {len(waypoints)} waypoints")
    print()

def run_pattern(pattern_name):
    """Run a specific waypoint pattern"""
    if pattern_name not in WAYPOINT_PATTERNS:
        print(f"Error: Pattern '{pattern_name}' not found")
        print_available_patterns()
        return
        
    waypoints = WAYPOINT_PATTERNS[pattern_name]
    print(f"Running pattern '{pattern_name}' with waypoints:")
    for i, wp in enumerate(waypoints):
        print(f"  {i+1}: {wp}")
    print()
    
    rclpy.init()
    navigator = WaypointNavigator()
    
    try:
        navigator.navigate_waypoints(waypoints, set_initial_pose=True)
    except KeyboardInterrupt:
        navigator.get_logger().info('Navigation interrupted by user')
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

def main():
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python3 waypoint_examples.py <pattern_name>")
        print()
        print_available_patterns()
        return
        
    pattern_name = sys.argv[1]
    run_pattern(pattern_name)

if __name__ == '__main__':
    main()