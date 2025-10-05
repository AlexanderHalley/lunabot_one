#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    update_rate = LaunchConfiguration('update_rate')
    publish_markers = LaunchConfiguration('publish_markers')

    # Declare launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true'
    )

    declare_update_rate_cmd = DeclareLaunchArgument(
        'update_rate',
        default_value='10.0',
        description='Zone detection update rate in Hz'
    )

    declare_publish_markers_cmd = DeclareLaunchArgument(
        'publish_markers',
        default_value='true',
        description='Publish RViz markers for zone visualization'
    )

    # Zone detector node
    zone_detector_node = Node(
        package='lunabot_one',
        executable='zone_detector.py',
        name='zone_detector',
        output='screen',
        parameters=[
            {
                'use_sim_time': use_sim_time,
                'update_rate': update_rate,
                'publish_markers': publish_markers
            }
        ]
    )

    return LaunchDescription([
        declare_use_sim_time_cmd,
        declare_update_rate_cmd,
        declare_publish_markers_cmd,
        zone_detector_node
    ])
