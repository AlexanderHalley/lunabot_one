#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist

class SkidSteerJoyTeleop(Node):
    def __init__(self):
        super().__init__('lunabot_joy_teleop')

        # Declare parameters with defaults
        self.declare_parameter('enable_button', 5)
        self.declare_parameter('axis_linear.x', 3)
        self.declare_parameter('axis_angular.yaw', 2)
        self.declare_parameter('scale_linear.x', 1.0)
        self.declare_parameter('scale_angular.yaw', -1.0)
        self.declare_parameter('max_linear_vel', 2.0)
        self.declare_parameter('max_angular_vel', 1.5)

        # Get parameter values
        self.enable_button = self.get_parameter('enable_button').value
        self.linear_axis = self.get_parameter('axis_linear.x').value
        self.angular_axis = self.get_parameter('axis_angular.yaw').value
        self.linear_scale = self.get_parameter('scale_linear.x').value
        self.angular_scale = self.get_parameter('scale_angular.yaw').value
        self.max_linear_vel = self.get_parameter('max_linear_vel').value
        self.max_angular_vel = self.get_parameter('max_angular_vel').value

        # Publisher to twist_mux input (change topic to '/cmd_vel_joy' to match your twist_mux config)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel_joy', 10)

        # Subscribe to joystick input
        self.joy_sub = self.create_subscription(Joy, '/joy', self.joy_callback, 10)

        self.get_logger().info('Lunabot Joy Teleop Node Started')
        self.get_logger().info(f'Enable button index: {self.enable_button}')

    def joy_callback(self, msg: Joy):
        # Check if the enable button is pressed
        if len(msg.buttons) <= self.enable_button or msg.buttons[self.enable_button] != 1:
            self.publish_zero_twist()
            return

        # Get axis values safely
        linear = msg.axes[self.linear_axis] if len(msg.axes) > self.linear_axis else 0.0
        angular = msg.axes[self.angular_axis] if len(msg.axes) > self.angular_axis else 0.0

        # Scale velocities
        linear_vel = linear * self.linear_scale * self.max_linear_vel
        angular_vel = angular * self.angular_scale * self.max_angular_vel

        # Publish Twist
        twist = Twist()
        twist.linear.x = linear_vel
        twist.angular.z = angular_vel
        self.cmd_vel_pub.publish(twist)

    def publish_zero_twist(self):
        twist = Twist()
        self.cmd_vel_pub.publish(twist)

def main(args=None):
    rclpy.init(args=args)
    node = SkidSteerJoyTeleop()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
