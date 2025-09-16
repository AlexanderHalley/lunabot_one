#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():

    # Lidar scan merger node
    lidar_merger_node = Node(
        package='ira_laser_tools',
        executable='laserscan_multi_merger',
        name='lidar_merger',
        parameters=[{
            'destination_frame': 'base_link',
            'cloud_destination_topic': '/merged_cloud',
            'scan_destination_topic': '/scan',
            'laserscan_topics': '/scan /scan_left /scan_right',
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.00436,  # ~0.25 degrees
            'scan_time': 0.1,
            'range_min': 0.2,
            'range_max': 8.0,
        }],
        remappings=[
            ('merged_cloud', '/merged_cloud'),
            ('scan', '/scan_merged')
        ]
    )

    return LaunchDescription([
        lidar_merger_node
    ])