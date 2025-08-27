import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    use_sim_time = LaunchConfiguration('use_sim_time')
    
    declare_use_sim_time_argument = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation/Gazebo clock')

    # Set environment variable for RTAB-Map to use more memory
    set_env_var = SetEnvironmentVariable('RTABMAP_DISABLE_ROS_CONSOLE_LOG', '1')

    # RTAB-Map SLAM node - RGB-D only first
    rtabmap_slam = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        parameters=[{
            'use_sim_time': use_sim_time,
            'subscribe_depth': True,
            'subscribe_rgb': True,
            'subscribe_scan': False,  # Disable scan for now
            'subscribe_scan_cloud': False,
            'subscribe_user_data': False,
            'subscribe_odom_info': False,
            'approx_sync': True,
            'wait_imu_to_init': False,
            
            # Frame IDs
            'frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'map_frame_id': 'map',
            
            # Sync parameters - very lenient for simulation
            'queue_size': 200,
            'sync_queue_size': 200,
            'topic_queue_size': 50,
            'approx_sync_max_interval': 1.0,  # Allow 1 second sync window
            'qos_image': 2,  # Best effort
            'qos_scan': 2,
            'qos_odom': 2,
            'qos_camera_info': 2,
            
            # Memory management
            'Mem/RehearsalSimilarity': '0.30',
            'Mem/RecentWmRatio': '0.2',
            'Mem/STMSize': '30',
            'Mem/LazyCreation': 'true',
            
            # Loop closure
            'Kp/MaxFeatures': '400',
            'Kp/DetectorStrategy': '0',  # SURF
            'Vis/MinInliers': '15',
            'Vis/InlierDistance': '0.1',
            'RGBD/OptimizeFromGraphEnd': 'false',
            'RGBD/ProximityPathMaxNeighbors': '10',
            'Reg/Strategy': '0',  # Vis
            'Reg/Force3DoF': 'true',  # 2D SLAM mode
            
            # Grid parameters for 2D occupancy grid
            'Grid/FromDepth': 'false',  # Use laser scan for grid
            'Grid/3D': 'false',
            'Grid/RangeMax': '12.0',
            'Grid/RangeMin': '0.1',
            'Grid/CellSize': '0.05',
            
            # Optimization
            'RGBD/OptimizeMaxError': '3.0',
            'Optimizer/GravitySigma': '0.3',
        }],
        remappings=[
            ('rgb/image', '/camera/image_raw'),
            ('depth/image', '/camera/depth/image_raw'),
            ('rgb/camera_info', '/camera/camera_info'),
            ('odom', '/odom')
        ],
        arguments=['--delete_db_on_start'],  # Start fresh each time
        output='screen'
    )

    # RTAB-Map visualization node  
    rtabmap_viz = Node(
        package='rtabmap_viz',
        executable='rtabmap_viz',
        name='rtabmap_viz',
        parameters=[{
            'use_sim_time': use_sim_time,
            'subscribe_depth': True,
            'subscribe_rgb': True,
            'subscribe_scan': False,  # Disable scan for now
            'subscribe_odom_info': False,
            'approx_sync': True,
            'frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'map_frame_id': 'map',
            'queue_size': 200,
            'sync_queue_size': 200,
            'approx_sync_max_interval': 1.0,  # Match main RTABMap sync window
            'qos_image': 2,
        }],
        remappings=[
            ('rgb/image', '/camera/image_raw'),
            ('depth/image', '/camera/depth/image_raw'),
            ('rgb/camera_info', '/camera/camera_info'),
            ('odom', '/odom')
        ],
        output='screen'
    )

    return LaunchDescription([
        set_env_var,
        declare_use_sim_time_argument,
        rtabmap_slam,
        rtabmap_viz
    ])