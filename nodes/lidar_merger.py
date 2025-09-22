#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
import numpy as np
import math
from rclpy.qos import QoSProfile, ReliabilityPolicy

class LidarMerger(Node):
    def __init__(self):
        super().__init__('lidar_merger')

        # QoS profile for sensors
        qos = QoSProfile(depth=10)
        qos.reliability = ReliabilityPolicy.BEST_EFFORT

        # Subscribers for each lidar
        self.front_sub = self.create_subscription(
            LaserScan, '/scan', self.front_callback, qos)
        self.left_sub = self.create_subscription(
            LaserScan, '/scan_left', self.left_callback, qos)
        self.right_sub = self.create_subscription(
            LaserScan, '/scan_right', self.right_callback, qos)

        # Publisher for merged scan
        self.merged_pub = self.create_publisher(LaserScan, '/scan_merged', 10)

        # Store latest scans
        self.front_scan = None
        self.left_scan = None
        self.right_scan = None

        # Physical positions of lidars relative to base_link (in meters)
        # Based on URDF: front at front edge, sides at midpoint on edges
        self.front_position = np.array([0.9652, 0.0])      # Front edge of chassis
        self.left_position = np.array([0.4826, 0.2484])    # Left side, halfway along length
        self.right_position = np.array([0.4826, -0.2484])  # Right side, halfway along length

        # Orientations (in radians)
        self.front_orientation = 0.0        # Facing forward
        self.left_orientation = math.pi/2   # Facing left (90 degrees)
        self.right_orientation = -math.pi/2 # Facing right (-90 degrees)

        # Timer to publish merged scans
        self.timer = self.create_timer(0.1, self.merge_and_publish)  # 10Hz

        self.get_logger().info('Lidar merger node started with position-aware fusion')

    def front_callback(self, msg):
        self.front_scan = msg

    def left_callback(self, msg):
        self.left_scan = msg

    def right_callback(self, msg):
        self.right_scan = msg

    def merge_and_publish(self):
        if not all([self.front_scan, self.left_scan, self.right_scan]):
            return

        # Create merged scan message
        merged_scan = LaserScan()
        merged_scan.header.stamp = self.get_clock().now().to_msg()
        merged_scan.header.frame_id = 'base_link'

        # Set scan parameters for 360 degrees
        merged_scan.angle_min = -math.pi
        merged_scan.angle_max = math.pi
        merged_scan.angle_increment = math.radians(1.0)  # 1 degree resolution
        merged_scan.time_increment = 0.0
        merged_scan.scan_time = 0.1
        merged_scan.range_min = 0.2
        merged_scan.range_max = 8.0

        # Initialize ranges array (360 points)
        num_points = int((merged_scan.angle_max - merged_scan.angle_min) / merged_scan.angle_increment)
        ranges = [float('inf')] * num_points

        # Process front lidar
        if self.front_scan:
            self.add_scan_to_merged(self.front_scan, ranges, self.front_position, self.front_orientation, merged_scan)

        # Process left lidar
        if self.left_scan:
            self.add_scan_to_merged(self.left_scan, ranges, self.left_position, self.left_orientation, merged_scan)

        # Process right lidar
        if self.right_scan:
            self.add_scan_to_merged(self.right_scan, ranges, self.right_position, self.right_orientation, merged_scan)

        merged_scan.ranges = ranges
        merged_scan.intensities = []

        self.merged_pub.publish(merged_scan)

    def add_scan_to_merged(self, scan, ranges, lidar_position, lidar_orientation, merged_scan):
        """Add a lidar scan to the merged ranges array with proper coordinate transformation"""
        for i, range_val in enumerate(scan.ranges):
            if math.isfinite(range_val) and scan.range_min <= range_val <= scan.range_max:
                # Calculate angle in the lidar's local frame
                local_angle = scan.angle_min + i * scan.angle_increment

                # Convert polar to cartesian in lidar's local frame
                local_x = range_val * math.cos(local_angle)
                local_y = range_val * math.sin(local_angle)

                # Transform to global frame (base_link)
                # Rotate by lidar orientation
                cos_orient = math.cos(lidar_orientation)
                sin_orient = math.sin(lidar_orientation)

                rotated_x = local_x * cos_orient - local_y * sin_orient
                rotated_y = local_x * sin_orient + local_y * cos_orient

                # Translate by lidar position
                global_x = rotated_x + lidar_position[0]
                global_y = rotated_y + lidar_position[1]

                # Convert back to polar from base_link origin
                global_range = math.sqrt(global_x**2 + global_y**2)
                global_angle = math.atan2(global_y, global_x)

                # Normalize angle to [-pi, pi]
                while global_angle > math.pi:
                    global_angle -= 2 * math.pi
                while global_angle < -math.pi:
                    global_angle += 2 * math.pi

                # Find corresponding index in merged scan
                merged_index = int((global_angle - merged_scan.angle_min) / merged_scan.angle_increment)

                if 0 <= merged_index < len(ranges):
                    # Take minimum range (closest obstacle)
                    if ranges[merged_index] == float('inf') or global_range < ranges[merged_index]:
                        ranges[merged_index] = global_range

def main(args=None):
    rclpy.init(args=args)
    lidar_merger = LidarMerger()

    try:
        rclpy.spin(lidar_merger)
    except KeyboardInterrupt:
        pass
    finally:
        lidar_merger.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()