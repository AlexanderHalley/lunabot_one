#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, TimerAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Package directories
    pkg_lunabot_one = get_package_share_directory('lunabot_one')
    
    # Launch configuration variables
    test_mode = LaunchConfiguration('test_mode')
    can_monitor = LaunchConfiguration('can_monitor')
    
    # Declare launch arguments
    declare_test_mode_cmd = DeclareLaunchArgument(
        'test_mode',
        default_value='basic',
        choices=['basic', 'motors', 'can', 'full'],
        description='Test mode: basic, motors, can, or full'
    )
    
    declare_can_monitor_cmd = DeclareLaunchArgument(
        'can_monitor',
        default_value='true',
        description='Enable CAN traffic monitoring'
    )
    
    # CAN setup
    can_setup_cmd = ExecuteProcess(
        cmd=['sudo', os.path.join(pkg_lunabot_one, 'hardware', 'can', 'can_setup.sh')],
        name='can_setup',
        output='screen'
    )
    
    # CAN traffic monitor (helpful for debugging)
    can_monitor_cmd = ExecuteProcess(
        condition=IfCondition(can_monitor),
        cmd=['candump', 'can0'],
        name='can_monitor',
        output='screen'
    )
    
    # Basic system test nodes
    robot_description_content = open(os.path.join(pkg_lunabot_one, 'urdf', 'robot.urdf.xacro')).read()
    robot_description = {'robot_description': robot_description_content}
    
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            robot_description,
            {'use_sim_time': False}
        ]
    )
    
    # Controller manager for hardware testing
    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        name='controller_manager',
        output='screen',
        parameters=[
            os.path.join(pkg_lunabot_one, 'config', 'control', 'hardware', 'hardware_controllers.yaml'),
            {'use_sim_time': False}
        ],
    )
    
    # Load joint state broadcaster (delayed start)
    joint_state_broadcaster_spawner = TimerAction(
        period=5.0,  # Wait 5 seconds after control node starts
        actions=[
            Node(
                package='controller_manager', 
                executable='spawner',
                arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
                output='screen'
            )
        ]
    )
    
    # Load diff_drive_controller (delayed start)  
    diff_drive_spawner = TimerAction(
        period=7.0,  # Wait 7 seconds to ensure hardware is ready
        actions=[
            Node(
                package='controller_manager',
                executable='spawner', 
                arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
                output='screen'
            )
        ]
    )
    
    # Keyboard teleop for manual testing
    teleop_keyboard_node = Node(
        package='teleop_twist_keyboard',
        executable='teleop_twist_keyboard',
        name='teleop_keyboard',
        output='screen',
        prefix='xterm -e',  # Run in separate terminal
        remappings=[
            ('/cmd_vel', '/diff_drive_controller/cmd_vel_unstamped')
        ]
    )
    
    # Test velocity publisher (for automated testing)
    test_velocity_node = Node(
        package='lunabot_one',
        executable='test_motor_velocity.py',  # Custom test script
        name='test_velocity_publisher',
        output='screen',
        parameters=[
            {'test_duration': 10.0},
            {'max_linear_vel': 0.5},
            {'max_angular_vel': 0.5}
        ]
    )
    
    # Diagnostic nodes for monitoring system health
    diagnostic_node = Node(
        package='diagnostic_aggregator',
        executable='aggregator_node',
        name='diagnostic_aggregator',
        output='screen'
    )
    
    # Create the launch description and populate
    ld = LaunchDescription()
    
    # Add the commands to the launch description
    ld.add_action(declare_test_mode_cmd)
    ld.add_action(declare_can_monitor_cmd)
    
    # Setup and monitoring
    ld.add_action(can_setup_cmd)
    ld.add_action(can_monitor_cmd)
    
    # Core system
    ld.add_action(robot_state_publisher_node)
    ld.add_action(control_node)
    ld.add_action(joint_state_broadcaster_spawner)
    ld.add_action(diff_drive_spawner)
    
    # Testing interfaces
    ld.add_action(teleop_keyboard_node)
    # ld.add_action(test_velocity_node)  # Uncomment when test script is ready
    ld.add_action(diagnostic_node)
    
    return ld