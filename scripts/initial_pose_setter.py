#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
import math

class InitialPoseSetter(Node):
    def __init__(self):
        super().__init__('initial_pose_setter')
        
        # Declare parameters
        self.declare_parameter('initial_pose_x', 1.0)
        self.declare_parameter('initial_pose_y', 1.0)
        self.declare_parameter('initial_pose_yaw', 0.0)
        
        # Get parameters
        self.initial_x = self.get_parameter('initial_pose_x').get_parameter_value().double_value
        self.initial_y = self.get_parameter('initial_pose_y').get_parameter_value().double_value
        self.initial_yaw = self.get_parameter('initial_pose_yaw').get_parameter_value().double_value
        
        # Publisher for initial pose
        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/initialpose',
            10
        )
        
        # Timer to publish initial pose after a delay
        self.timer = self.create_timer(3.0, self.publish_initial_pose)
        self.published = False
        
        self.get_logger().info(f'Initial pose setter ready: ({self.initial_x}, {self.initial_y}, {self.initial_yaw})')
    
    def publish_initial_pose(self):
        if self.published:
            return
            
        pose_msg = PoseWithCovarianceStamped()
        pose_msg.header.frame_id = "map"
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        
        # Position
        pose_msg.pose.pose.position.x = self.initial_x
        pose_msg.pose.pose.position.y = self.initial_y
        pose_msg.pose.pose.position.z = 0.0
        
        # Orientation (convert yaw to quaternion)
        qw = math.cos(self.initial_yaw / 2.0)
        qz = math.sin(self.initial_yaw / 2.0)
        pose_msg.pose.pose.orientation.x = 0.0
        pose_msg.pose.pose.orientation.y = 0.0
        pose_msg.pose.pose.orientation.z = qz
        pose_msg.pose.pose.orientation.w = qw
        
        # Covariance matrix
        pose_msg.pose.covariance = [0.0] * 36
        pose_msg.pose.covariance[0] = 0.25   # x variance
        pose_msg.pose.covariance[7] = 0.25   # y variance  
        pose_msg.pose.covariance[35] = 0.06853892326654787  # yaw variance
        
        self.initial_pose_pub.publish(pose_msg)
        self.get_logger().info(f'Published initial pose: ({self.initial_x}, {self.initial_y}, {self.initial_yaw})')
        
        self.published = True
        
        # Shutdown after publishing
        self.timer.cancel()
        self.create_timer(1.0, self.shutdown_node)
    
    def shutdown_node(self):
        self.get_logger().info('Initial pose set successfully. Shutting down.')
        rclpy.shutdown()

def main():
    rclpy.init()
    node = InitialPoseSetter()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()

if __name__ == '__main__':
    main()