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

    # SLAM Toolbox node with merged scan and 8m range limit
    slam_toolbox_node = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            {
                'use_sim_time': use_sim_time,
                'odom_frame': 'odom',
                'map_frame': 'map',
                'base_frame': 'base_link',  # Changed from base_footprint - must match scan frame_id
                'scan_topic': '/scan_merged',
                'mode': 'mapping',

                # Range limiting to 8m
                'minimum_travel_distance': 0.1,
                'minimum_travel_heading': 0.1,
                'scan_buffer_size': 20,
                'scan_buffer_maximum_scan_distance': 8.0,
                'max_laser_range': 8.0,
                'minimum_time_interval': 0.3,

                # Resolution and quality
                'resolution': 0.05,
                'map_update_interval': 1.0,

                # Loop closure - more aggressive to fix drift
                'do_loop_closing': True,
                'loop_search_maximum_distance': 5.0,
                'loop_match_minimum_chain_size': 5,
                'loop_match_minimum_response_coarse': 0.5,
                'loop_match_minimum_response_fine': 0.6,

                # Scan matching - more lenient for better alignment
                'use_scan_matching': True,
                'use_scan_barycenter': True,
                'minimum_angle_penalty': 0.7,
                'minimum_distance_penalty': 0.3,

                # Correlation parameters - wider search for better loop closure
                'correlation_search_space_dimension': 0.8,
                'correlation_search_space_resolution': 0.01,
                'correlation_search_space_smear_deviation': 0.1,

                # Coarse search
                'coarse_search_angle_offset': 0.349,
                'coarse_angle_resolution': 0.0349,

                # General parameters
                'solver_plugin': 'solver_plugins::CeresSolver',
                'ceres_linear_solver': 'SPARSE_NORMAL_CHOLESKY',
                'ceres_preconditioner': 'SCHUR_JACOBI',
                'ceres_trust_strategy': 'LEVENBERG_MARQUARDT',
                'ceres_dogleg_type': 'TRADITIONAL_DOGLEG',
                'ceres_loss_function': 'None'
            }
        ],
        remappings=[
            ('/scan', '/scan_merged')
        ]
    )

    # Lifecycle manager to auto-start SLAM Toolbox
    lifecycle_manager = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_slam',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'autostart': True},
            {'bond_timeout': 10.0},  # Increased from default 4.0s to allow SLAM initialization
            {'attempt_respawn_reconnection': True},  # Try to reconnect if bond fails
            {'bond_respawn_max_duration': 10.0},
            {'node_names': ['slam_toolbox']}
        ]
    )

    return LaunchDescription([
        declare_use_sim_time_cmd,
        slam_toolbox_node,
        lifecycle_manager
    ])
