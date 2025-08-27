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
                                       'config', 'params', 'mapper_params_online_async.yaml')

    declare_use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation/Gazebo clock')
    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=default_params_file,
        description='Full path to the ROS2 parameters file to use for the slam_toolbox node')

    # If the provided param file doesn't have slam_toolbox params, we must pass the
    # default_params_file instead. This could happen due to automatic propagation of
    # LaunchArguments. See:
    # https://github.com/ros-planning/navigation2/pull/2243#issuecomment-800479866
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
            'min_height': -0.5,
            'max_height': 2.0,
            'angle_min': -1.5708,  # -90 degrees
            'angle_max': 1.5708,   # 90 degrees
            'angle_increment': 0.0087,  # 0.5 degrees
            'scan_time': 0.3333,
            'range_min': 0.05,
            'range_max': 8.0,
            'use_inf': True,
            'inf_epsilon': 1.0
        }],
        remappings=[
            ('cloud_in', '/camera/depth/points'),
            ('scan', '/camera/scan')
        ],
        output='screen'
    )

    start_async_slam_toolbox_node = Node(
        parameters=[
          actual_params_file,
          {'use_sim_time': use_sim_time}
        ],
        package='slam_toolbox',
        executable='sync_slam_toolbox_node',
        name='slam_toolbox',
        output='screen')

    configure_slam_toolbox = ExecuteProcess(
        cmd=['ros2', 'service', 'call', '/slam_toolbox/change_state', 
             'lifecycle_msgs/srv/ChangeState', '{transition: {id: 1}}'],
        output='screen'
    )

    activate_slam_toolbox = TimerAction(
        period=2.0,
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
    ld.add_action(start_async_slam_toolbox_node)
    ld.add_action(configure_slam_toolbox)
    ld.add_action(activate_slam_toolbox)

    return ld

  # Configure
  #ros2 service call /slam_toolbox/change_state lifecycle_msgs/srv/ChangeState "{transition: {id: 1}}"

  # Activate  
  #ros2 service call /slam_toolbox/change_state lifecycle_msgs/srv/ChangeState "{transition: {id: 3}}"
