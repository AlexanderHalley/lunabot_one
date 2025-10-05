#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_dir = get_package_share_directory('lunabot_one')

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Declare launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    # Depth image to LaserScan converter
    depthimage_to_laserscan = Node(
        package='depthimage_to_laserscan',
        executable='depthimage_to_laserscan_node',
        name='depthimage_to_laserscan',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time,
            'output_frame': 'camera_link_optical',
            'scan_time': 0.033,  # 30Hz depth camera
            'range_min': 0.2,
            'range_max': 8.0,
            'scan_height': 10,  # Number of rows to use from depth image
        }],
        remappings=[
            ('depth', '/camera/depth/image'),
            ('depth_camera_info', '/camera/camera_info'),
            ('scan', '/camera/scan')
        ]
    )

    # Merged sensors node (combines lidar_merger output + camera scan)
    merged_sensors = Node(
        package='lunabot_one',
        executable='merged_sensors.py',
        name='merged_sensors',
        output='screen',
        parameters=[{
            'use_sim_time': use_sim_time
        }]
    )

    return LaunchDescription([
        declare_use_sim_time_cmd,
        depthimage_to_laserscan,
        merged_sensors
    ])
