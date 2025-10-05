#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Get directories
    pkg_dir = get_package_share_directory('lunabot_one')
    
    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml_file = LaunchConfiguration('map')
    
    # Declare launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_dir, 'maps', 'arena_map.yaml'),
        description='Full path to map yaml file to load'
    )

    declare_autoset_pose_cmd = DeclareLaunchArgument(
        'autoset_pose',
        default_value='true',
        description='Automatically set initial pose for arena (true/false)'
    )

    autoset_pose = LaunchConfiguration('autoset_pose')
    
    # Include localization (AMCL + Map Server)
    localization_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_dir, 'launch', 'localization_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'map': map_yaml_file
        }.items()
    )
    
    # Include navigation stack (delayed to allow localization to start first)
    navigation_cmd = TimerAction(
        period=8.0,  # Wait 8 seconds for localization to be ready
        actions=[
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    os.path.join(pkg_dir, 'launch', 'navigation_launch.py')
                ),
                launch_arguments={
                    'use_sim_time': use_sim_time
                }.items()
            )
        ]
    )

    # Initial pose setter (delayed to allow AMCL to start)
    initial_pose_setter = TimerAction(
        period=10.0,
        actions=[
            Node(
                package='lunabot_one',
                executable='initial_pose_setter',
                name='initial_pose_setter',
                output='screen',
                parameters=[{
                    'use_sim_time': use_sim_time,
                    'initial_pose_x': 1.0,
                    'initial_pose_y': 1.0,
                    'initial_pose_yaw': 0.0
                }]
            )
        ]
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # Add the commands to the launch description
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_map_yaml_cmd)
    ld.add_action(declare_autoset_pose_cmd)

    ld.add_action(localization_cmd)
    ld.add_action(navigation_cmd)
    ld.add_action(initial_pose_setter)

    return ld