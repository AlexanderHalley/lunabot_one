from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

import os
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    params_file = os.path.join(get_package_share_directory('lunabot_one'), 'config', 'control', 'joystick.yaml')

    joy_node = Node(
        package='joy',
        executable='joy_node',
        parameters=[params_file, {'use_sim_time': use_sim_time}],
    )

    teleop_node = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',  # must match the key in YAML
        parameters=[params_file, {'use_sim_time': use_sim_time}],
        remappings=[('/cmd_vel', '/cmd_vel_joy')],
    )

    # Remove twist_stamper since we're using twist_mux for command routing
    # twist_stamper = Node(
    #     package='twist_stamper',
    #     executable='twist_stamper',
    #     parameters=[{'use_sim_time': use_sim_time}],
    #     remappings=[
    #         ('/cmd_vel_in', '/cmd_vel_joy'),
    #         ('/cmd_vel_out', '/diff_cont/cmd_vel'),
    #     ]
    # )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),
        joy_node,
        teleop_node
    ])
