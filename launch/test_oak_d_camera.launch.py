#!/usr/bin/env python3
"""
OAK-D S2 Camera Standalone Test Launch File

This launch file provides a simple, self-contained way to test the OAK-D S2 camera
with RViz2 visualization. It's designed for quick troubleshooting and validation
without requiring the full hardware stack.

Usage:
    ros2 launch lunabot_one test_oak_d_camera.launch.py
    ros2 launch lunabot_one test_oak_d_camera.launch.py show_depth:=true
    ros2 launch lunabot_one test_oak_d_camera.launch.py rviz:=false

Topics Published:
    - /camera/color/image_raw: RGB images
    - /camera/color/camera_info: RGB camera calibration
    - /camera/stereo/depth: Depth images
    - /camera/stereo/camera_info: Depth camera calibration
    - /camera/stereo/points: 3D point cloud (if enabled)
    - /tf: Camera transform frames

RViz Configuration:
    The launch file auto-generates a minimal RViz config for viewing:
    - RGB image from /camera/color/image_raw
    - Depth image (colorized) from /camera/stereo/depth
    - 3D point cloud from /camera/stereo/points
    - Camera frame visualization
"""

import os
from pathlib import Path
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    OpaqueFunction,
    LogInfo,
)
from launch.substitutions import (
    LaunchConfiguration,
    FindPackageShare,
    PathJoinSubstitution,
)
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    """Setup launch description with conditional nodes."""

    # Get launch arguments
    camera_enabled = LaunchConfiguration("camera_enabled").perform(context)
    show_rgb = LaunchConfiguration("show_rgb").perform(context)
    show_depth = LaunchConfiguration("show_depth").perform(context)
    show_pointcloud = LaunchConfiguration("show_pointcloud").perform(context)
    use_rviz = LaunchConfiguration("rviz").perform(context)
    log_level = LaunchConfiguration("log_level").perform(context)

    package_share = FindPackageShare("lunabot_one").perform(context)
    config_dir = PathJoinSubstitution(
        [FindPackageShare("lunabot_one"), "config", "camera"]
    ).perform(context)

    nodes = []

    # Node 1: OAK-D Camera Driver
    if camera_enabled == "true":
        depthai_node = Node(
            package="depthai_ros",
            executable="rgb_stereo_node",
            namespace="camera",
            name="oak_d_driver",
            parameters=[
                os.path.join(config_dir, "oak_d_s2.yaml"),
                {
                    "stereo_depth.align_depth": "rgb",
                    "stereo_depth.depth_lower_threshold": 400,
                    "stereo_depth.depth_upper_threshold": 5000,
                    "rgb.fps": 30,
                    "stereo_depth.fps": 30,
                },
            ],
            remappings=[
                ("color/image", "color/image_raw"),
                ("color/camera_info", "color/camera_info"),
                ("depth/image", "stereo/depth"),
                ("depth/camera_info", "stereo/camera_info"),
            ],
            output="screen",
            arguments=["--ros-args", "--log-level", log_level],
        )
        nodes.append(depthai_node)
        nodes.append(
            LogInfo(
                msg="Starting OAK-D S2 camera driver. Check output for any USB/firmware errors."
            )
        )
    else:
        nodes.append(LogInfo(msg="Camera disabled. Set camera_enabled:=true to enable."))

    # Node 2: Robot State Publisher (for camera frames)
    urdf_file = os.path.join(package_share, "urdf", "lunabot_hardware.urdf.xacro")
    if not os.path.exists(urdf_file):
        # Fallback to description URDF
        urdf_file = os.path.join(
            package_share, "description", "robot.urdf.xacro"
        )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[
            {
                "robot_description": open(urdf_file).read(),
                "use_sim_time": False,
            }
        ],
        output="screen",
    )
    nodes.append(robot_state_publisher)

    # Node 3: RViz2 Visualization
    if use_rviz == "true":
        # Create minimal RViz config for camera testing
        rviz_config = create_rviz_config(show_rgb, show_depth, show_pointcloud)
        rviz_config_file = os.path.join("/tmp", "oak_d_test.rviz")
        with open(rviz_config_file, "w") as f:
            f.write(rviz_config)

        rviz_node = Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", rviz_config_file],
            output="log",
        )
        nodes.append(rviz_node)
        nodes.append(LogInfo(msg=f"RViz2 config saved to: {rviz_config_file}"))

    return nodes


def create_rviz_config(show_rgb: str, show_depth: str, show_pointcloud: str) -> str:
    """Generate a minimal RViz config for camera testing."""
    return f"""Panels:
  - Class: rviz_common/Displays
    Help Height: 78
    Name: Displays
    Property Tree Widget:
      Expanded:
        - /Global Options1
        - /Status1
        - /TF1
        - /Image1
      Splitter Ratio: 0.5
    Tree Height: 363
  - Class: rviz_common/Selection
    Name: Selection
  - Class: rviz_common/Tool Properties
    Expanded:
      - /2D Goal Pose1
      - /Publish Point1
    Name: Tool Properties
    Splitter Ratio: 0.5
  - Class: rviz_common/Views
    Expanded:
      - /Current View1
    Name: Views
    Splitter Ratio: 0.5
Visualization Manager:
  Class: ""
  Displays:
    - Alpha: 0.5
      Cell Size: 1
      Class: rviz_common/Grid
      Color: 160; 160; 164
      Enabled: true
      Line Style:
        Line Width: 0.029999999329447746
        Value: Lines
      Name: Grid
      Normal Cell Count: 0
      Offset:
        X: 0
        Y: 0
        Z: 0
      Plane: XY
      Plane Cell Count: 10
      Reference Frame: <Fixed Frame>
      Value: true
    - Class: rviz_common/TF
      Enabled: true
      Frame Timeout: 15
      Frames:
        All Enabled: true
        camera_link:
          Value: true
        camera_rgb_optical_frame:
          Value: true
        camera_stereo_optical_frame:
          Value: true
      Marker Alpha: 1
      Marker Scale: 0.5
      Name: TF
      Show Arrows: true
      Show Axes: true
      Show Names: false
      Tree:
        camera_link:
          camera_rgb_optical_frame: {{}}
          camera_stereo_optical_frame: {{}}
      Update Interval: 0
      Value: true
    - Class: rviz_common/Image
      Enabled: {show_rgb.lower()}
      Image Topic: /camera/color/image_raw
      Max Value: 1
      Median window: 5
      Min Value: 0
      Name: RGB Image
      Transport Hint: raw
      Value: {show_rgb.lower()}
    - Class: rviz_common/Image
      Enabled: {show_depth.lower()}
      Image Topic: /camera/stereo/depth
      Max Value: 5000
      Median window: 5
      Min Value: 0
      Name: Depth Image
      Transport Hint: raw
      Value: {show_depth.lower()}
    - Alpha: 1
      Autoselect Decay Time: 0
      Autosize: true
      Background Color: 0; 0; 0
      Class: rviz_common/PointCloud2
      Color: 200; 200; 200
      Color Transformer: ""
      Decay Time: 0
      Enabled: {show_pointcloud.lower()}
      Invert Rainbow: false
      Max Color: 255; 255; 255
      Max Intensity: -1
      Min Color: 0; 0; 0
      Min Intensity: 0
      Name: Point Cloud
      Position Transformer: ""
      Selectable: true
      Size (Pixels): 3
      Size (m): 0.01
      Style: Flat Squares
      Topic: /camera/stereo/points
      Unreliable: false
      Use Fixed Frame: true
      Use rainbow: true
      Value: {show_pointcloud.lower()}
  Enabled: true
  Global Options:
    Background Color: 48; 48; 48
    Fixed Frame: camera_link
    Frame Rate: 30
  Name: root
  Tools:
    - Class: rviz_common/Interact
      Hide Inactive Objects: true
    - Class: rviz_common/MoveCamera
    - Class: rviz_common/Select
    - Class: rviz_common/FocusCamera
    - Class: rviz_common/Measure
      Class Name: rviz_common/Measure
    - Class: rviz_ros_plugin/Publish
      Class Name: rviz_ros_plugin/Publish
  Value: true
  Views:
    Current:
      Class: rviz_common/Orbit
      Distance: 1
      Enable Stereo Rendering:
        Stereo Eye Separation: 0.05999999865889549
        Stereo Focal Distance: 1
        Swap Stereo Eyes: false
        Value: false
      Focal Point:
        X: 0
        Y: 0
        Z: 0
      Focal Shape Fixed Size: true
      Focal Shape Size: 0.05000000074505806
      Invert Z Axis: false
      Name: Current View
      Near Clip Distance: 0.009999999776482582
      Pitch: 0
      Target Frame: camera_link
      Value: Orbit (rviz)
      Yaw: 0
    Saved Views: {{}}
Window Geometry:
  Displays:
    collapsed: false
  Height: 1016
  Hide Left Dock: false
  Hide Right Dock: false
  Image:
    collapsed: false
  QMainWindow State: 000000ff00000000fd0000000100000000000002fc000003f6fc0200000003fc0000004c0000015e0000010fc020000000fa000000030000000fe0000000000fffffffa000000010100000002fb00000014004900 6d006100670065005f0031ffffffff0000015e000000000000000bfb0000001600440065007000740068005f0069006d0061006700650000000264000001390000015f00ffffffff0000000000000400000004f0000003f6000000040000000800000008fc00000000
  Selection:
    collapsed: false
  Tool Properties:
    collapsed: true
  Views:
    collapsed: false
  Width: 1920
"""


def generate_launch_description() -> LaunchDescription:
    """Generate the launch description."""

    return LaunchDescription(
        [
            # Launch Arguments
            DeclareLaunchArgument(
                "camera_enabled",
                default_value="true",
                description="Enable OAK-D camera driver (true/false)",
            ),
            DeclareLaunchArgument(
                "show_rgb",
                default_value="true",
                description="Display RGB image in RViz (true/false)",
            ),
            DeclareLaunchArgument(
                "show_depth",
                default_value="false",
                description="Display depth image in RViz (true/false)",
            ),
            DeclareLaunchArgument(
                "show_pointcloud",
                default_value="false",
                description="Display point cloud in RViz (true/false)",
            ),
            DeclareLaunchArgument(
                "rviz",
                default_value="true",
                description="Launch RViz2 for visualization (true/false)",
            ),
            DeclareLaunchArgument(
                "log_level",
                default_value="INFO",
                description="ROS logging level (DEBUG/INFO/WARN/ERROR)",
            ),
            # Setup function to conditionally add nodes
            OpaqueFunction(function=launch_setup),
        ]
    )
