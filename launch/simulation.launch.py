import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    package_name = 'lunabot_one'

    rsp = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'rsp.launch.py')
        ]),
        launch_arguments={'use_sim_time': 'true', 'use_ros2_control': 'true'}.items()
    )

    joystick = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory(package_name), 'launch', 'joystick.launch.py')
        ]),
        launch_arguments={'use_sim_time': 'true'}.items()
    )

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

    # Default world
    default_world = os.path.join(
        get_package_share_directory(package_name),
        'worlds',
        'obstacles.world'
    )

    world = LaunchConfiguration('world')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=default_world,
        description='World to load'
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={
            'gz_args': ['-r -v0 ', world],
            'on_exit_shutdown': 'true'
        }.items()
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'my_bot', '-z', '0.2'],
        output='screen'
    )

    # Spawner for joint_state_broadcaster (delayed to ensure controller manager is ready)
    joint_broad_spawner = TimerAction(
        period=3.0,
        actions=[
            Node(
                package="controller_manager",
                executable="spawner",
                arguments=["joint_broad"]
            )
        ]
    )

    # ✅ New diff_drive_controller spawner
    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_drive_controller"]
    )

    # ros_gz_bridge config
    bridge_params = os.path.join(get_package_share_directory(package_name), 'config', 'gz_bridge.yaml')
    ros_gz_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ]
    )

    # Bridge for RGB image (match actual Gazebo topic)
    ros_gz_image_bridge = Node(
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
        output='screen'
    )
    
    # Bridge for point cloud (use actual Gazebo topic with frame correction)
    ros_gz_pointcloud_bridge = Node(
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
        output='screen'
    )
    
    
    # Bridge for camera info
    ros_gz_camera_info_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "camera/camera_info@sensor_msgs/msg/CameraInfo@gz.msgs.CameraInfo"
        ],
        output='screen'
    )

    ros_gz_imu_bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        arguments=[
            "/imu@sensor_msgs/msg/Imu@gz.msgs.IMU"
        ],
        parameters=[{"use_sim_time": True},
        ]
    )

    # Removed: four_wheel_drive_controller

    # Disabled custom lunabot_joy_teleop - using standard teleop_twist_joy instead
    # joy_teleop_node = Node(
    #     package='lunabot_one',
    #     executable='lunabot_joy_teleop',
    #     name='lunabot_joy_teleop',
    #     output='screen',
    #     parameters=[{'use_sim_time': True}]
    # )

    # Relay node to convert Twist to TwistStamped
    twist_relay = Node(
        package='lunabot_one',
        executable='twist_to_stamped_relay',
        name='twist_to_stamped_relay',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        rsp,
        joystick,
        twist_mux,
        world_arg,
        gazebo,
        spawn_entity,
        joint_broad_spawner,
        diff_drive_spawner,
        ros_gz_bridge,
        ros_gz_image_bridge,
        ros_gz_pointcloud_bridge,
        ros_gz_camera_info_bridge,
        ros_gz_imu_bridge, 
        twist_relay,  # Convert Twist to TwistStamped
        # joy_teleop_node,  # Disabled - using standard teleop instead
    ])
