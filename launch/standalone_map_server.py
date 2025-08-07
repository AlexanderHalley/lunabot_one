#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Get directories
    pkg_dir = get_package_share_directory('lunabot_one')
    
    # Launch configuration variables
    map_yaml_file = LaunchConfiguration('map')
    
    # Declare launch arguments
    declare_map_yaml_cmd = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(pkg_dir, 'maps', 'saved_map.yaml'),
        description='Full path to map yaml file to load'
    )
    
    # Simple map server node
    map_server_cmd = Node(
        package='nav2_map_server',
        executable='map_server',
        name='standalone_map_server',
        output='screen',
        parameters=[
            {'yaml_filename': map_yaml_file},
            {'use_sim_time': True}
        ],
        remappings=[
            ('/map', '/rviz_map')
        ]
    )
    
    # Lifecycle manager for the map server
    lifecycle_manager_cmd = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='standalone_lifecycle_manager',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'autostart': True},
            {'node_names': ['standalone_map_server']}
        ]
    )
    
    # Create the launch description
    ld = LaunchDescription()
    
    # Add the commands to the launch description
    ld.add_action(declare_map_yaml_cmd)
    ld.add_action(map_server_cmd)
    ld.add_action(lifecycle_manager_cmd)
    
    return ld