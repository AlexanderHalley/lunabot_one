#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped
from builtin_interfaces.msg import Time

class TwistToStampedRelay(Node):
    def __init__(self):
        super().__init__('twist_to_stamped_relay')
        
        # Publisher for stamped messages
        self.stamped_pub = self.create_publisher(
            TwistStamped, 
            '/diff_drive_controller/cmd_vel', 
            10
        )
        
        # Subscriber for unstamped messages
        self.twist_sub = self.create_subscription(
            Twist,
            '/cmd_vel_unstamped',
            self.twist_callback,
            10
        )
        
        self.get_logger().info('Twist to TwistStamped relay node started')
    
    def twist_callback(self, msg: Twist):
        # Convert Twist to TwistStamped
        stamped_msg = TwistStamped()
        stamped_msg.header.stamp = self.get_clock().now().to_msg()
        stamped_msg.header.frame_id = "base_link"
        stamped_msg.twist = msg
        
        self.stamped_pub.publish(stamped_msg)

def main(args=None):
    rclpy.init(args=args)
    node = TwistToStampedRelay()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()