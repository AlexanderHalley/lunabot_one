#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Package directories
    pkg_lunabot_one = get_package_share_directory('lunabot_one')
    
    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    auto_can_setup = LaunchConfiguration('auto_can_setup')
    
    # Declare launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation (Gazebo) clock if true'
    )
    
    declare_auto_can_setup_cmd = DeclareLaunchArgument(
        'auto_can_setup',
        default_value='true',
        description='Automatically setup CAN interface on launch'
    )
    
    # CAN interface setup (requires sudo privileges)
    can_setup_cmd = ExecuteProcess(
        condition=IfCondition(auto_can_setup),
        cmd=['sudo', os.path.join(pkg_lunabot_one, 'hardware', 'can', 'can_setup.sh')],
        name='can_setup',
        output='screen'
    )
    
    # Robot description
    robot_description_content = open(os.path.join(pkg_lunabot_one, 'urdf', 'robot.urdf.xacro')).read()
    robot_description = {'robot_description': robot_description_content}
    
    # Robot State Publisher
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            robot_description,
            {'use_sim_time': use_sim_time}
        ]
    )
    
    # ODrive ROS2 Control Hardware Interface
    # This assumes you have the ODrive ROS2 Control package installed
    control_node = Node(
        package='controller_manager',
        executable='ros2_control_node',
        name='controller_manager',
        output='screen',
        parameters=[
            os.path.join(pkg_lunabot_one, 'config', 'control', 'hardware', 'hardware_controllers.yaml'),
            {'use_sim_time': use_sim_time}
        ],
    )
    
    # Load diff_drive_controller
    diff_drive_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['diff_drive_controller', '--controller-manager', '/controller_manager'],
        output='screen'
    )
    
    # Load joint_state_broadcaster  
    joint_state_broadcaster_spawner = Node(
        package='controller_manager', 
        executable='spawner',
        arguments=['joint_state_broadcaster', '--controller-manager', '/controller_manager'],
        output='screen'
    )
    
    # Joy/Teleop nodes (optional)
    joy_node = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time}
        ]
    )
    
    teleop_twist_joy_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time}
        ],
        remappings=[
            ('/cmd_vel', '/diff_drive_controller/cmd_vel_unstamped')
        ]
    )
    
    # Create the launch description and populate
    ld = LaunchDescription()
    
    # Add the commands to the launch description
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_auto_can_setup_cmd)
    
    # CAN setup (conditional)
    ld.add_action(can_setup_cmd)
    
    # Core nodes
    ld.add_action(robot_state_publisher_node)
    ld.add_action(control_node)
    ld.add_action(joint_state_broadcaster_spawner)
    ld.add_action(diff_drive_spawner)
    
    # Teleop (optional)
    ld.add_action(joy_node)
    ld.add_action(teleop_twist_joy_node)
    
    return ld