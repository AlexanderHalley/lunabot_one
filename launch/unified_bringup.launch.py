#!/usr/bin/env python3

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction, GroupAction
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'lunabot_one'

    # Launch arguments
    use_hardware_arg = DeclareLaunchArgument(
        'use_hardware',
        default_value='false',
        description='Use hardware (true) or simulation (false)'
    )

    sim_mode_arg = DeclareLaunchArgument(
        'sim_mode',
        default_value='true', 
        description='Enable simulation-specific sensors (depth camera, IMU)'
    )

    use_ros2_control_arg = DeclareLaunchArgument(
        'use_ros2_control',
        default_value='true',
        description='Use ros2_control for robot control'
    )

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=os.path.join(
            get_package_share_directory(package_name),
            'worlds',
            'obstacles.world'
        ),
        description='World file to load in simulation'
    )

    # Get launch configurations
    use_hardware = LaunchConfiguration('use_hardware')
    sim_mode = LaunchConfiguration('sim_mode')
    use_ros2_control = LaunchConfiguration('use_ros2_control')
    world = LaunchConfiguration('world')

    # Robot State Publisher - unified for both modes
    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'rsp.launch.py')
        ]),
        launch_arguments={
            'use_sim_time': PythonExpression(["'false' if '", use_hardware, "' == 'true' else 'true'"]),
            'use_ros2_control': use_ros2_control,
            'sim_mode': sim_mode,
            'use_hardware': use_hardware
        }.items()
    )

    # Joystick control (common to both modes)
    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'joystick.launch.py')
        ]),
        launch_arguments={
            'use_sim_time': PythonExpression(["'false' if '", use_hardware, "' == 'true' else 'true'"])
        }.items()
    )

    # Twist Mux (common to both modes)
    twist_mux_params = os.path.join(get_package_share_directory(package_name), 'config', 'control', 'twist_mux.yaml')
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {
            'use_sim_time': PythonExpression(["False if '", use_hardware, "' == 'true' else True"]),
            'use_stamped': False,
            'publish_stamped': False
        }],
        remappings=[('/cmd_vel_out', '/cmd_vel_unstamped')]
    )

    # SIMULATION MODE GROUP
    simulation_group = GroupAction([
        
        # Gazebo simulation
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([
                os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
            ]),
            launch_arguments={
                'gz_args': ['-r -v0 ', world],
                'on_exit_shutdown': 'true'
            }.items()
        ),

        # Spawn robot entity in simulation
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-topic', 'robot_description', '-name', 'my_bot', '-z', '0.2'],
            output='screen'
        ),

        # Joint state broadcaster spawner (delayed)
        TimerAction(
            period=3.0,
            actions=[
                Node(
                    package="controller_manager",
                    executable="spawner",
                    arguments=["joint_broad"]
                )
            ]
        ),

        # Diff drive controller spawner
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["diff_drive_controller"]
        ),

        # Gazebo-ROS bridges
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                '--ros-args',
                '-p',
                f'config_file:={os.path.join(get_package_share_directory(package_name), "config", "gz_bridge.yaml")}',
            ]
        ),

        # Image bridge for camera
        Node(
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
        ),

        # Point cloud bridge
        Node(
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
        ),

        # Camera info bridge
        Node(
            package="ros_gz_bridge",
            executable="parameter_bridge",
            arguments=[
                "camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo"
            ],
            output='screen',
            condition=IfCondition(sim_mode)
        ),

        # Twist to stamped relay
        Node(
            package='lunabot_one',
            executable='twist_to_stamped_relay',
            name='twist_to_stamped_relay',
            output='screen',
            parameters=[{'use_sim_time': True}]
        ),

    ], condition=UnlessCondition(use_hardware))

    # HARDWARE MODE GROUP  
    hardware_group = GroupAction([
        
        # Hardware-specific controller spawners
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster"],
            output='screen'
        ),

        Node(
            package="controller_manager",
            executable="spawner",  
            arguments=["differential_drive_controller"],
            output='screen'
        ),

        # Hardware lidar node (replace with actual lidar driver)
        # Node(
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
        # ),

    ], condition=IfCondition(use_hardware))

    return LaunchDescription([
        use_hardware_arg,
        sim_mode_arg, 
        use_ros2_control_arg,
        world_arg,
        rsp,
        joystick,
        twist_mux,
        simulation_group,
        hardware_group,
    ])