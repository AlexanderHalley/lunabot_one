#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TwistStamped
from sensor_msgs.msg import JointState
import math

class TurningDiagnostics(Node):
    def __init__(self):
        super().__init__('turning_diagnostics')
        
        # Subscribers for diagnostics
        self.cmd_vel_sub = self.create_subscription(
            Twist, '/cmd_vel', self.cmd_vel_callback, 10)
        self.controller_cmd_sub = self.create_subscription(
            TwistStamped, '/diff_drive_controller/cmd_vel', self.controller_cmd_callback, 10)
        self.joint_states_sub = self.create_subscription(
            JointState, '/joint_states', self.joint_states_callback, 10)
        
        # Store previous angle for rotation tracking
        self.total_rotation = 0.0
        self.last_yaw = None
        
        self.get_logger().info('Turning diagnostics node started')
    
    def cmd_vel_callback(self, msg: Twist):
        if abs(msg.angular.z) > 0.1:  # Only log when turning
            self.get_logger().info(f'Gazebo cmd_vel: linear={msg.linear.x:.3f}, angular={msg.angular.z:.3f}')
    
    def controller_cmd_callback(self, msg: TwistStamped):
        if abs(msg.twist.angular.z) > 0.1:  # Only log when turning
            self.get_logger().info(f'Controller cmd_vel: linear={msg.twist.linear.x:.3f}, angular={msg.twist.angular.z:.3f}')
    
    def joint_states_callback(self, msg: JointState):
        # Find wheel joints
        wheel_joints = {}
        for i, name in enumerate(msg.name):
            if 'wheel_joint' in name and i < len(msg.velocity):
                wheel_joints[name] = {
                    'position': msg.position[i] if i < len(msg.position) else 0.0,
                    'velocity': msg.velocity[i]
                }
        
        if wheel_joints:
            # Check if any wheels are moving
            max_vel = max([abs(joint['velocity']) for joint in wheel_joints.values()])
            
            if max_vel > 0.1:  # Only log when wheels are moving
                vel_str = ', '.join([f"{name}: {joint['velocity']:.3f}" for name, joint in wheel_joints.items()])
                self.get_logger().info(f'Wheel velocities: {vel_str}')
                
                # Calculate approximate rotation from wheel positions
                if 'left_wheel_joint' in wheel_joints and 'right_wheel_joint' in wheel_joints:
                    left_pos = wheel_joints['left_wheel_joint']['position']
                    right_pos = wheel_joints['right_wheel_joint']['position']
                    
                    # Simple differential drive yaw calculation
                    wheel_separation = 0.782
                    wheel_radius = 0.1778
                    yaw = (right_pos - left_pos) * wheel_radius / wheel_separation
                    
                    if self.last_yaw is not None:
                        delta_yaw = yaw - self.last_yaw
                        # Handle wrap-around
                        if delta_yaw > math.pi:
                            delta_yaw -= 2 * math.pi
                        elif delta_yaw < -math.pi:
                            delta_yaw += 2 * math.pi
                        
                        self.total_rotation += abs(delta_yaw)
                        
                        if self.total_rotation > 0:
                            degrees = math.degrees(self.total_rotation)
                            if abs(max_vel) < 0.05:  # Wheels stopped
                                self.get_logger().warn(f'WHEELS STOPPED after {degrees:.1f} degrees rotation!')
                    
                    self.last_yaw = yaw

def main(args=None):
    rclpy.init(args=args)
    node = TurningDiagnostics()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()