#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np
import math
from rclpy.qos import QoSProfile, ReliabilityPolicy

class MergedSensors(Node):
    def __init__(self):
        super().__init__('merged_sensors')

        # QoS profile for sensors
        qos = QoSProfile(depth=10)
        qos.reliability = ReliabilityPolicy.BEST_EFFORT

        # Subscribe to merged lidar scan (3 LiDARs already combined)
        self.lidar_sub = self.create_subscription(
            LaserScan, '/scan_merged', self.lidar_callback, qos)

        # Subscribe to depth camera scan (converted from depth image)
        self.camera_sub = self.create_subscription(
            LaserScan, '/camera/scan', self.camera_callback, qos)

        # Publisher for final merged scan (use same QoS as subscribers for consistency)
        self.final_pub = self.create_publisher(LaserScan, '/scan_final', qos)

        # Store latest scans
        self.lidar_scan = None
        self.camera_scan = None

        # Timer to publish merged scans
        self.timer = self.create_timer(0.1, self.merge_and_publish)  # 10Hz

        self.get_logger().info('Merged sensors node started - combining LiDAR and depth camera')

    def lidar_callback(self, msg):
        self.lidar_scan = msg

    def camera_callback(self, msg):
        self.camera_scan = msg

    def merge_and_publish(self):
        # If we have lidar data, publish with or without camera
        if not self.lidar_scan:
            return

        # Create final scan message based on lidar
        final_scan = LaserScan()
        final_scan.header.stamp = self.get_clock().now().to_msg()
        final_scan.header.frame_id = 'base_link'

        # Use lidar scan parameters (360 degrees)
        final_scan.angle_min = self.lidar_scan.angle_min
        final_scan.angle_max = self.lidar_scan.angle_max
        final_scan.angle_increment = self.lidar_scan.angle_increment
        final_scan.time_increment = 0.0
        final_scan.scan_time = 0.1
        final_scan.range_min = 0.2
        final_scan.range_max = 8.0

        # Start with lidar ranges
        num_points = len(self.lidar_scan.ranges)
        ranges = list(self.lidar_scan.ranges)

        # Merge camera data if available
        if self.camera_scan:
            self.merge_camera_into_scan(self.camera_scan, ranges, final_scan)
            self.get_logger().debug('Merged camera and lidar data')
        else:
            self.get_logger().debug('Publishing lidar-only data (no camera)')

        final_scan.ranges = ranges
        final_scan.intensities = []

        self.final_pub.publish(final_scan)

    def merge_camera_into_scan(self, camera_scan, ranges, final_scan):
        """Merge camera scan into the ranges array, taking minimum distances"""
        for i, range_val in enumerate(camera_scan.ranges):
            if math.isfinite(range_val) and camera_scan.range_min <= range_val <= camera_scan.range_max:
                # Calculate angle of this camera measurement
                camera_angle = camera_scan.angle_min + i * camera_scan.angle_increment

                # Find corresponding index in final scan
                final_index = int((camera_angle - final_scan.angle_min) / final_scan.angle_increment)

                if 0 <= final_index < len(ranges):
                    # Take minimum range (closest obstacle)
                    if not math.isfinite(ranges[final_index]) or range_val < ranges[final_index]:
                        ranges[final_index] = range_val

def main(args=None):
    rclpy.init(args=args)
    merged_sensors = MergedSensors()

    try:
        rclpy.spin(merged_sensors)
    except KeyboardInterrupt:
        pass
    finally:
        merged_sensors.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
