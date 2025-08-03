#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64MultiArray
import math

class FourWheelDriveController(Node):
    def __init__(self):
        super().__init__('four_wheel_drive_controller')
        
        # Robot parameters (from your URDF)
        self.wheel_radius = 0.033
        self.wheel_separation_y = 0.297
        self.wheel_separation_x = 0.452
        # distance between front and rear wheels
        
        # Subscribe to cmd_vel
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # Publishers for individual wheel controllers
        self.left_front_pub = self.create_publisher(
            Float64MultiArray,
            '/left_front_wheel_velocity_controller/commands',
            10
        )
        self.right_front_pub = self.create_publisher(
            Float64MultiArray,
            '/right_front_wheel_velocity_controller/commands',
            10
        )
        self.left_rear_pub = self.create_publisher(
            Float64MultiArray,
            '/left_rear_wheel_velocity_controller/commands',
            10
        )
        self.right_rear_pub = self.create_publisher(
            Float64MultiArray,
            '/right_rear_wheel_velocity_controller/commands',
            10
        )
        
        self.get_logger().info('4-Wheel Drive Controller started')
    
    def cmd_vel_callback(self, msg):
        # Extract linear and angular velocities
        linear_x = msg.linear.x
        angular_z = msg.angular.z
        
        # Calculate wheel velocities using skid-steer kinematics
        # For skid steer: all wheels on same side move at same speed
        
        # Linear component (same for all wheels)
        linear_vel = linear_x / self.wheel_radius
        
        # Angular component (opposite for left/right sides)
        angular_vel = (angular_z * self.wheel_separation_y / 2.0) / self.wheel_radius
        
        # Calculate individual wheel velocities
        left_wheel_vel = linear_vel - angular_vel
        right_wheel_vel = linear_vel + angular_vel
        
        # Create messages
        left_front_msg = Float64MultiArray()
        left_front_msg.data = [left_wheel_vel]
        
        right_front_msg = Float64MultiArray()
        right_front_msg.data = [right_wheel_vel]
        
        left_rear_msg = Float64MultiArray()
        left_rear_msg.data = [left_wheel_vel]
        
        right_rear_msg = Float64MultiArray()
        right_rear_msg.data = [right_wheel_vel]
        
        # Publish commands
        self.left_front_pub.publish(left_front_msg)
        self.right_front_pub.publish(right_front_msg)
        self.left_rear_pub.publish(left_rear_msg)
        self.right_rear_pub.publish(right_rear_msg)
        
        # Debug output
        self.get_logger().debug(
            f'Cmd: linear={linear_x:.2f}, angular={angular_z:.2f} | '
            f'Wheels: left={left_wheel_vel:.2f}, right={right_wheel_vel:.2f}'
        )

def main(args=None):
    rclpy.init(args=args)
    node = FourWheelDriveController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()