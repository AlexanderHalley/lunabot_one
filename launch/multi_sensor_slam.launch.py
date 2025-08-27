import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, LogInfo, ExecuteProcess, TimerAction
from launch.conditions import UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from nav2_common.launch import HasNodeParams


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    default_params_file = os.path.join(get_package_share_directory("lunabot_one"),
                                       'config', 'params', 'mapper_params_multi_sensor.yaml')

    declare_use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation/Gazebo clock')
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=default_params_file,
        description='Full path to the ROS2 parameters file to use for the slam_toolbox node')

    has_node_params = HasNodeParams(source_file=params_file,
                                    node_name='slam_toolbox')

    actual_params_file = PythonExpression(['"', params_file, '" if ', has_node_params,
                                           ' else "', default_params_file, '"'])

    log_param_change = LogInfo(msg=['provided params_file ',  params_file,
                                    ' does not contain slam_toolbox parameters. Using default: ',
                                    default_params_file],
                               condition=UnlessCondition(has_node_params))

    # Convert depth camera point cloud to laser scan
    pointcloud_to_scan = Node(
        package='pointcloud_to_laserscan',
        executable='pointcloud_to_laserscan_node',
        name='pointcloud_to_laserscan',
        parameters=[{
            'target_frame': 'base_link',
            'transform_tolerance': 0.01,
            'min_height': -0.3,  # Focus on robot height level
            'max_height': 1.5,   # Avoid ceiling/high objects
            'angle_min': -0.7854,  # -45 degrees (camera FOV limited)
            'angle_max': 0.7854,   # 45 degrees 
            'angle_increment': 0.0087,  # 0.5 degrees
            'scan_time': 0.1,
            'range_min': 0.1,
            'range_max': 6.0,  # Shorter range for indoor mapping
            'use_inf': True,
            'inf_epsilon': 1.0,
            'use_sim_time': use_sim_time
        }],
        remappings=[
            ('cloud_in', '/camera/depth/points'),
            ('scan', '/camera/scan')
        ],
        output='screen'
    )

    # Merge LiDAR and camera laser scans
    laser_scan_merger = Node(
        package='ira_laser_tools',
        executable='laserscan_multi_merger',
        name='laser_scan_merger',
        parameters=[{
            'destination_frame': 'base_link',
            'cloud_destination_topic': '/merged_cloud',
            'scan_destination_topic': '/merged_scan',
            'laserscan_topics': '/scan /camera/scan',
            'angle_min': -3.14159,
            'angle_max': 3.14159,
            'angle_increment': 0.0087,
            'scan_time': 0.1,
            'range_min': 0.05,
            'range_max': 12.0,
            'use_sim_time': use_sim_time
        }],
        output='screen'
    )

    # SLAM Toolbox using merged scan
    start_async_slam_toolbox_node = Node(
        parameters=[
          actual_params_file,
          {'use_sim_time': use_sim_time}
        ],
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        remappings=[
            ('scan', '/merged_scan')  # Use merged scan instead of just LiDAR
        ],
        output='screen')

    configure_slam_toolbox = ExecuteProcess(
        cmd=['ros2', 'service', 'call', '/slam_toolbox/change_state', 
             'lifecycle_msgs/srv/ChangeState', '{transition: {id: 1}}'],
        output='screen'
    )

    activate_slam_toolbox = TimerAction(
        period=3.0,  # Give merger time to start
        actions=[
            ExecuteProcess(
                cmd=['ros2', 'service', 'call', '/slam_toolbox/change_state', 
                     'lifecycle_msgs/srv/ChangeState', '{transition: {id: 3}}'],
                output='screen'
            )
        ]
    )

    ld = LaunchDescription()

    ld.add_action(declare_use_sim_time_argument)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(log_param_change)
    ld.add_action(pointcloud_to_scan)
    ld.add_action(laser_scan_merger)
    ld.add_action(start_async_slam_toolbox_node)
    ld.add_action(configure_slam_toolbox)
    ld.add_action(activate_slam_toolbox)

    return ld