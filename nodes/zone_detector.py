#!/usr/bin/env python3

"""
Zone Detector Node

Detects which arena zone the robot is currently in based on its map coordinates.
Publishes current zone and provides RViz visualization of zone boundaries.

Arena zones (from arena_waypoints.py):
- Starting zone: (0,0) to (2,2) - Green L-shape boundary
- Excavation zone: (2,0) to (2.5,5) - Left side of black divider
- Obstacle zone: (2.5,0) to (6.8,5) - Right side with boulders
- Construction zone: (3.88,0) to (6.8,1.5) - Black L-shape boundary
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import TransformStamped
from visualization_msgs.msg import Marker, MarkerArray
from tf2_ros import TransformListener, Buffer
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
import math


class ZoneDetector(Node):
    # Zone definitions with priority (lower = checked first)
    # Starting zone is a 2x2 area wholly contained in excavation zone
    ZONES = {
        'starting': {
            'bounds': {'x': (0.0, 2.0), 'y': (0.0, 2.0)},
            'priority': 1,  # Check first - most specific
            'color': {'r': 0.0, 'g': 1.0, 'b': 0.0, 'a': 0.3}  # Green
        },
        'construction': {
            'bounds': {'x': (3.88, 6.8), 'y': (0.0, 1.5)},
            'priority': 2,
            'color': {'r': 0.0, 'g': 0.0, 'b': 0.0, 'a': 0.3}  # Black
        },
        'excavation': {
            'bounds': {'x': (0.0, 2.5), 'y': (0.0, 5.0)},  # Extended to x=0 to contain starting zone
            'priority': 3,
            'color': {'r': 0.8, 'g': 0.6, 'b': 0.4, 'a': 0.3}  # Brown
        },
        'obstacle': {
            'bounds': {'x': (2.5, 6.8), 'y': (0.0, 5.0)},
            'priority': 4,
            'color': {'r': 1.0, 'g': 0.0, 'b': 0.0, 'a': 0.2}  # Red
        }
    }

    def __init__(self):
        super().__init__('zone_detector')

        # Parameters
        self.declare_parameter('update_rate', 10.0)
        self.declare_parameter('publish_markers', True)

        update_rate = self.get_parameter('update_rate').value
        self.publish_markers = self.get_parameter('publish_markers').value

        # TF2 setup
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Publishers
        self.zone_pub = self.create_publisher(String, '/current_zone', 10)

        if self.publish_markers:
            self.marker_pub = self.create_publisher(MarkerArray, '/zone_markers', 10)
            # Publish static zone markers once at startup and periodically
            self.marker_timer = self.create_timer(5.0, self.publish_zone_markers)

        # State tracking
        self.current_zone = 'unknown'
        self.last_zone = 'unknown'

        # Timer for zone detection
        self.detection_timer = self.create_timer(1.0 / update_rate, self.detect_zone)

        self.get_logger().info('=' * 60)
        self.get_logger().info('Zone Detector Started')
        self.get_logger().info('=' * 60)
        self.get_logger().info(f'Update rate: {update_rate} Hz')
        self.get_logger().info(f'Publishing markers: {self.publish_markers}')
        self.get_logger().info('')
        self.get_logger().info('IMPORTANT: Zone detection requires navigation to be running!')
        self.get_logger().info('Please ensure you have started full navigation:')
        self.get_logger().info('  make full-nav')
        self.get_logger().info('     OR')
        self.get_logger().info('  ros2 launch lunabot_one full_navigation_launch.py')
        self.get_logger().info('=' * 60)

        # Publish initial markers
        if self.publish_markers:
            self.publish_zone_markers()

    def point_in_bounds(self, x, y, bounds):
        """Check if point (x, y) is within the given bounds"""
        return (bounds['x'][0] <= x <= bounds['x'][1] and
                bounds['y'][0] <= y <= bounds['y'][1])

    def get_robot_position(self):
        """Get robot position from map frame"""
        try:
            transform = self.tf_buffer.lookup_transform(
                'map',
                'base_link',
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.5)
            )

            x = transform.transform.translation.x
            y = transform.transform.translation.y
            return x, y

        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().debug(f'Could not get transform: {e}')
            return None, None

    def detect_zone(self):
        """Detect which zone the robot is currently in"""
        x, y = self.get_robot_position()

        if x is None or y is None:
            return

        # Check zones in priority order
        zone_found = False
        sorted_zones = sorted(self.ZONES.items(), key=lambda item: item[1]['priority'])

        for zone_name, zone_info in sorted_zones:
            if self.point_in_bounds(x, y, zone_info['bounds']):
                self.current_zone = zone_name
                zone_found = True
                break

        if not zone_found:
            self.current_zone = 'out_of_bounds'

        # Publish current zone
        zone_msg = String()
        zone_msg.data = self.current_zone
        self.zone_pub.publish(zone_msg)

        # Log zone transitions
        if self.current_zone != self.last_zone:
            self.get_logger().info(
                f'Zone transition: {self.last_zone} -> {self.current_zone} '
                f'(position: {x:.2f}, {y:.2f})'
            )
            self.last_zone = self.current_zone

    def publish_zone_markers(self):
        """Publish RViz markers showing zone boundaries"""
        marker_array = MarkerArray()

        for i, (zone_name, zone_info) in enumerate(self.ZONES.items()):
            bounds = zone_info['bounds']
            color = zone_info['color']

            # Create a cube marker for the zone
            marker = Marker()
            marker.header.frame_id = 'map'
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = 'zones'
            marker.id = i
            marker.type = Marker.CUBE
            marker.action = Marker.ADD

            # Position at center of zone
            center_x = (bounds['x'][0] + bounds['x'][1]) / 2.0
            center_y = (bounds['y'][0] + bounds['y'][1]) / 2.0
            marker.pose.position.x = center_x
            marker.pose.position.y = center_y
            marker.pose.position.z = 0.01  # Just above ground

            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0

            # Scale to zone size
            marker.scale.x = bounds['x'][1] - bounds['x'][0]
            marker.scale.y = bounds['y'][1] - bounds['y'][0]
            marker.scale.z = 0.02  # Very thin

            # Color
            marker.color.r = color['r']
            marker.color.g = color['g']
            marker.color.b = color['b']
            marker.color.a = color['a']

            marker.lifetime = rclpy.duration.Duration(seconds=10.0).to_msg()

            marker_array.markers.append(marker)

            # Add text label
            text_marker = Marker()
            text_marker.header.frame_id = 'map'
            text_marker.header.stamp = self.get_clock().now().to_msg()
            text_marker.ns = 'zone_labels'
            text_marker.id = i + 100
            text_marker.type = Marker.TEXT_VIEW_FACING
            text_marker.action = Marker.ADD

            text_marker.pose.position.x = center_x
            text_marker.pose.position.y = center_y
            text_marker.pose.position.z = 0.3  # Above the zone

            text_marker.scale.z = 0.3  # Text height

            text_marker.color.r = 1.0
            text_marker.color.g = 1.0
            text_marker.color.b = 1.0
            text_marker.color.a = 0.9

            text_marker.text = zone_name.upper()
            text_marker.lifetime = rclpy.duration.Duration(seconds=10.0).to_msg()

            marker_array.markers.append(text_marker)

        self.marker_pub.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    zone_detector = ZoneDetector()

    try:
        rclpy.spin(zone_detector)
    except KeyboardInterrupt:
        pass
    finally:
        zone_detector.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
