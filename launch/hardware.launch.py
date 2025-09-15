#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'lunabot_one'

    # Launch arguments - defaults set for hardware
    use_ros2_control_arg = DeclareLaunchArgument(
        'use_ros2_control',
        default_value='true',
        description='Use ros2_control for robot control'
    )

    # Get launch configurations
    use_ros2_control = LaunchConfiguration('use_ros2_control')

    # Robot State Publisher - configured for hardware
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'rsp.launch.py')
        ]),
        launch_arguments={
            'use_sim_time': 'false',
            'use_ros2_control': use_ros2_control,
            'sim_mode': 'false',
            'use_hardware': 'true'
        }.items()
    )

    # Joystick control
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'joystick.launch.py')
        ]),
        launch_arguments={
            'use_sim_time': 'false'
        }.items()
    )

    # Twist Mux
    twist_mux_params = os.path.join(get_package_share_directory(package_name), 'config', 'control', 'twist_mux.yaml')
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {
            'use_sim_time': False,
            'use_stamped': False,
            'publish_stamped': False
        }],
        remappings=[('/cmd_vel_out', '/cmd_vel_unstamped')]
    )

    # Hardware-specific controller spawners
    joint_state_broadcaster = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster"],
        output='screen'
    )

    differential_drive_controller = Node(
        package="controller_manager",
        executable="spawner",  
        arguments=["differential_drive_controller"],
        output='screen'
    )

    # Hardware lidar node (uncomment and configure for your specific lidar)
    # Example for LDLidar LD19
    # ldlidar_node = Node(
    #     package="ldlidar_stl_ros2",
    #     executable="ldlidar_stl_ros2_node", 
    #     name="ldlidar_publisher_ld19",
    #     output='screen',
    #     parameters=[
    #         {'product_name': 'LDLidar_LD19'},
    #         {'topic_name': 'scan'},
    #         {'port_name': '/dev/ttyUSB0'},
    #         {'port_baudrate': 230400},
    #         {'laser_scan_dir': True},
    #         {'enable_angle_crop_func': False},
    #         {'angle_crop_min': 135.0},
    #         {'angle_crop_max': 225.0}
    #     ]
    # )

    # Example for RPLidar
    # rplidar_node = IncludeLaunchDescription(
    #     PythonLaunchDescriptionSource([
    #         os.path.join(get_package_share_directory(package_name), 'launch', 'rplidar.launch.py')
    #     ])
    # )

    return LaunchDescription([
        use_ros2_control_arg,
        rsp,
        joystick,
        twist_mux,
        joint_state_broadcaster,
        differential_drive_controller,
        # ldlidar_node,  # Uncomment when using LDLidar
        # rplidar_node,  # Uncomment when using RPLidar
    ])