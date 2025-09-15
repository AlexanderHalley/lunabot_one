#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, GroupAction
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'lunabot_one'

    # Launch arguments - defaults set for simulation
    use_ros2_control_arg = DeclareLaunchArgument(
        'use_ros2_control',
        default_value='true',
        description='Use ros2_control for robot control'
    )

    sim_mode_arg = DeclareLaunchArgument(
        'sim_mode',
        default_value='true', 
        description='Enable simulation-specific sensors (depth camera, IMU)'
    )

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(
            get_package_share_directory(package_name),
            'worlds',
            'usc_arena.world'
        ),
        description='World file to load in simulation'
    )

    # Get launch configurations
    sim_mode = LaunchConfiguration('sim_mode')
    use_ros2_control = LaunchConfiguration('use_ros2_control')
    world = LaunchConfiguration('world')

    # Robot State Publisher - configured for simulation
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'rsp.launch.py')
        ]),
        launch_arguments={
            'use_sim_time': 'true',
            'use_ros2_control': use_ros2_control,
            'sim_mode': sim_mode,
            'use_hardware': 'false'
        }.items()
    )

    # Joystick control
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'joystick.launch.py')
        ]),
        launch_arguments={
            'use_sim_time': 'true'
        }.items()
    )

    # Twist Mux
    twist_mux_params = os.path.join(get_package_share_directory(package_name), 'config', 'control', 'twist_mux.yaml')
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {
            'use_sim_time': True,
            'use_stamped': False,
            'publish_stamped': False
        }],
        remappings=[('/cmd_vel_out', '/cmd_vel_unstamped')]
    )

    # Gazebo simulation
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={
            'gz_args': ['-r -v0 ', world],
            'on_exit_shutdown': 'true'
        }.items()
    )

    # Spawn robot entity in simulation
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'my_bot', '-x', '1', '-y', '1', '-z', '0.2'],
        output='screen'
    )

    # Joint state broadcaster spawner (delayed)
    joint_state_spawner = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=["joint_broad"]
            )
        ]
    )

    # Diff drive controller spawner
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"]
    )

    # Gazebo-ROS bridges
    gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={os.path.join(get_package_share_directory(package_name), "config", "gz_bridge.yaml")}',
        ]
    )

    # Image bridge for camera
    image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["camera/image", "camera/depth_image"],
        remappings=[
            ("camera/image", "camera/image_raw"),
            ("camera/depth_image", "camera/depth/image_raw")
        ],
        parameters=[{
            "qos_overrides./camera/image.subscription.reliability": "best_effort",
            "qos_overrides./camera/depth_image.subscription.reliability": "best_effort"
        }],
        output='screen',
        condition=IfCondition(sim_mode)
    )

    # Point cloud bridge
    pointcloud_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "camera/points@sensor_msgs/msg/PointCloud2@gz.msgs.PointCloudPacked"
        ],
        remappings=[
            ("camera/points", "camera/depth/points")
        ],
        parameters=[
            {"qos_overrides./camera/points.subscription.reliability": "best_effort"}
        ],
        output='screen',
        condition=IfCondition(sim_mode)
    )

    # Camera info bridge
    camera_info_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo"
        ],
        output='screen',
        condition=IfCondition(sim_mode)
    )

    # Twist to stamped relay
    twist_relay = Node(
        package='lunabot_one',
        executable='twist_to_stamped_relay',
        name='twist_to_stamped_relay',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        use_ros2_control_arg,
        sim_mode_arg,
        world_arg,
        rsp,
        joystick,
        twist_mux,
        gazebo_launch,
        spawn_entity,
        joint_state_spawner,
        diff_drive_spawner,
        gz_bridge,
        image_bridge,
        pointcloud_bridge,
        camera_info_bridge,
        twist_relay,
    ])