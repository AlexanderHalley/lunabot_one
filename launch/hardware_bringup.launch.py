#!/usr/bin/env python3

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Package directories
    pkg_lunabot_one = get_package_share_directory('lunabot_one')

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    auto_can_setup = LaunchConfiguration('auto_can_setup')
    can_interface = LaunchConfiguration('can_interface')

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

    declare_can_interface_cmd = DeclareLaunchArgument(
        'can_interface',
        default_value='can0',
        description='CAN interface name'
    )

    # CAN interface setup (requires sudo privileges)
    can_setup_cmd = ExecuteProcess(
        condition=IfCondition(auto_can_setup),
        cmd=['sudo', os.path.join(pkg_lunabot_one, 'hardware', 'can', 'can_setup.sh')],
        name='can_setup',
        output='screen'
    )

    # Robot State Publisher (reads URDF for visualization)
    urdf_file = os.path.join(pkg_lunabot_one, 'urdf', 'lunabot_hardware.urdf.xacro')
    with open(urdf_file, 'r') as f:
        robot_description_content = f.read()

    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            {'robot_description': robot_description_content},
            {'use_sim_time': use_sim_time}
        ]
    )

    # SparkFlex Driver Node (replaces ros2_control for direct CAN communication)
    sparkflex_driver_node = Node(
        package='lunabot_one',
        executable='sparkflex_driver_node',
        name='sparkflex_driver',
        output='screen',
        parameters=[
            {'use_sim_time': use_sim_time},
            {'can_interface': can_interface},
            {'wheel_separation': 0.7620},  # 30 inches
            {'wheel_radius': 0.1778},      # 7 inch wheels
            {'max_rpm': 5700.0},
            {'current_limit': 40},
            {'pid_p': 0.0001},
            {'pid_i': 0.0},
            {'pid_d': 0.0},
            {'pid_ff': 0.000176},
            # Motor CAN IDs
            {'front_left_id': 1},
            {'front_right_id': 2},
            {'rear_left_id': 3},
            {'rear_right_id': 4}
        ],
        remappings=[
            ('/cmd_vel', '/cmd_vel')
        ]
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
            ('/cmd_vel', '/cmd_vel')
        ]
    )

    # Create the launch description and populate
    ld = LaunchDescription()

    # Add the commands to the launch description
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_auto_can_setup_cmd)
    ld.add_action(declare_can_interface_cmd)

    # CAN setup (conditional)
    ld.add_action(can_setup_cmd)

    # Core nodes
    ld.add_action(robot_state_publisher_node)
    ld.add_action(sparkflex_driver_node)

    # Teleop (optional)
    ld.add_action(joy_node)
    ld.add_action(teleop_twist_joy_node)

    return ld
