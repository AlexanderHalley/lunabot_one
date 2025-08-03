import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
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

    twist_mux_params = os.path.join(get_package_share_directory(package_name), 'config', 'twist_mux.yaml')
    twist_mux = Node(
        package="twist_mux",
        executable="twist_mux",
        parameters=[twist_mux_params, {'use_sim_time': True}],
        remappings=[('/cmd_vel_out', '/cmd_vel')]
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
        arguments=['-topic', 'robot_description', '-name', 'my_bot', '-z', '0.1'],
        output='screen'
    )

    # Spawner for joint_state_broadcaster
    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"]
    )

    # ✅ Spawners for the 4 wheel controllers
    left_front_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["left_front_wheel_velocity_controller"]
    )

    right_front_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["right_front_wheel_velocity_controller"]
    )

    left_rear_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["left_rear_wheel_velocity_controller"]
    )

    right_rear_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["right_rear_wheel_velocity_controller"]
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

    ros_gz_image_bridge = Node(
        package="ros_gz_image",
        executable="image_bridge",
        arguments=["/camera/image_raw"]
    )

    four_wheel_controller = Node(
        package='lunabot_one',
        executable='four_wheel_drive_controller',
        name='four_wheel_drive_controller',
        output='screen',
        parameters=[{'use_sim_time': True}]
    )

    # Added lunabot_joy_teleop node here
    joy_teleop_node = Node(
        package='lunabot_one',
        executable='lunabot_joy_teleop',
        name='lunabot_joy_teleop',
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
        left_front_spawner,
        right_front_spawner,
        left_rear_spawner,
        right_rear_spawner,
        ros_gz_bridge,
        four_wheel_controller,
        joy_teleop_node,  # <-- Added teleop here
    ])
