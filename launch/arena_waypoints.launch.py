#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, ExecuteProcess
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    package_name = 'lunabot_one'
    pkg_dir = get_package_share_directory(package_name)
    
    # Launch arguments
    waypoint_pattern_arg = DeclareLaunchArgument(
        'pattern',
        default_value='arena_exploration',
        description='Waypoint pattern to execute (arena_exploration, arena_perimeter, etc.)'
    )
    
    map_file_arg = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_dir, 'maps', 'arena_map.yaml'),
        description='Map file to use for navigation'
    )

    # Launch navigation with arena map
    navigation_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(pkg_dir, 'launch', 'minimal_navigation_launch.py')
        ]),
        launch_arguments={
            'map': LaunchConfiguration('map')
        }.items()
    )
    
    # Execute waypoint pattern
    waypoint_execution = ExecuteProcess(
        cmd=['python3',
             os.path.join(pkg_dir, 'scripts', 'arena_waypoints.py'),
             LaunchConfiguration('pattern')],
        output='screen'
    )

    return LaunchDescription([
        waypoint_pattern_arg,
        map_file_arg,
        navigation_launch,
        waypoint_execution,
    ])