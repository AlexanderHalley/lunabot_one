import os

from launch import LaunchDescription
from launch_ros.actions import Node

'''
'Intent was to take /camera/depth/points messages published by the depth camera, 
and translate them from sensor_msgs/msgs/Image to sensor_msgs/msgs/Pointcloud2 for Rviz2 visualization'
Requires downloading depth_image_proc
To install, run: sudo apt install ros-jazzy-depth-image-proc

def generate_launch_description():

    return LaunchCescription([

        Node(
            package='depth_image_proc',
            executable='point_cloudexyzgrb_noe',
            name="point_cloud_xyzgrb",
            remappings=[
                ('points', '/camera/depth/pointcloud')
            ]
    )
    ])
'''
def generate_launch_description():



    return LaunchDescription([

        Node(
            package='v4l2_camera',
            executable='v4l2_camera_node',
            output='screen',
            namespace='camera',
            parameters=[{
                'image_size': [640,480],
                'time_per_frame': [1, 6],
                'camera_frame_id': 'camera_link_optical'
                }]
    )
    ])
