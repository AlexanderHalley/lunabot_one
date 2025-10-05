#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get the launch directory
    pkg_dir = get_package_share_directory('lunabot_one')
    
    # Launch arguments
    map_file_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_dir, 'maps', 'arena_map.yaml'),
        description='Path to the map file'
    )
    
    waypoints_arg = DeclareLaunchArgument(
        'waypoints',
        default_value='2.0 0.0 2.0 2.0 0.0 2.0 0.0 0.0',
        description='Space-separated list of waypoint coordinates (x1 y1 [yaw1] x2 y2 [yaw2] ...)'
    )
    
    auto_start_arg = DeclareLaunchArgument(
        'auto_start',
        default_value='true',
        description='Whether to automatically start waypoint navigation'
    )
    
    # Include the minimal navigation launch
    minimal_nav_launch = ExecuteProcess(
        cmd=['ros2', 'launch', 'lunabot_one', 'minimal_navigation_launch.py', 
             'map:=' + LaunchConfiguration('map').perform(None)],
        output='screen'
    )
    
    # Waypoint navigator node (only if auto_start is true)
    waypoint_navigator_node = ExecuteProcess(
        cmd=['python3', 
             os.path.join(pkg_dir, '..', '..', 'src', 'lunabot_one', 'scripts', 'waypoint_navigator.py')] + 
             LaunchConfiguration('waypoints').perform(None).split(),
        output='screen',
        condition=IfCondition(LaunchConfiguration('auto_start'))
    )
    
    return LaunchDescription([
        map_file_arg,
        waypoints_arg, 
        auto_start_arg,
        minimal_nav_launch,
        waypoint_navigator_node,
    ])