#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, DurabilityPolicy
from geometry_msgs.msg import Twist, TransformStamped
from std_msgs.msg import Float64MultiArray
from nav_msgs.msg import Odometry
from sensor_msgs.msg import JointState
from rclpy.duration import Duration
from tf2_ros import TransformBroadcaster
import tf_transformations
import math
import time

class FourWheelDriveController(Node):
    def __init__(self):
        super().__init__('four_wheel_drive_controller')
        
        # Robot parameters
        self.wheel_radius = 0.1778  # meters
        self.wheel_separation_y = 0.782  # side-to-side
        self.wheel_separation_x = 0.864  # front-to-back
        
        # Command timeout
        self.cmd_timeout_sec = 0.25  # Stop if no cmd_vel for this long
        self.last_cmd_time = self.get_clock().now()
        self.last_cmd_vel = Twist()  # Store the latest command
        
        # Odometry state
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.last_odom_time = self.get_clock().now()
        
        # Previous wheel positions for odometry calculation
        self.prev_left_pos = None
        self.prev_right_pos = None
        
        # Subscribers
        self.cmd_vel_sub = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )
        
        # Joint state subscription with compatible QoS
        from rclpy.qos import QoSProfile, DurabilityPolicy
        joint_state_qos = QoSProfile(depth=10)
        joint_state_qos.durability = DurabilityPolicy.VOLATILE  # Match what we saw in your topic echo
        
        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            joint_state_qos
        )
        
        # Publishers
        self.left_front_pub = self.create_publisher(Float64MultiArray, '/left_front_wheel_velocity_controller/commands', 10)
        self.right_front_pub = self.create_publisher(Float64MultiArray, '/right_front_wheel_velocity_controller/commands', 10)
        self.left_rear_pub = self.create_publisher(Float64MultiArray, '/left_rear_wheel_velocity_controller/commands', 10)
        self.right_rear_pub = self.create_publisher(Float64MultiArray, '/right_rear_wheel_velocity_controller/commands', 10)
        
        # Odometry publisher
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        
        # TF broadcaster
        self.tf_broadcaster = TransformBroadcaster(self)
        
        # Timer to continuously send commands
        self.timer = self.create_timer(0.05, self.publish_wheel_commands)  # 20 Hz
        
        self.get_logger().info('✅ 4-Wheel Drive Controller with Odometry started')

    def cmd_vel_callback(self, msg):
        self.last_cmd_vel = msg
        self.last_cmd_time = self.get_clock().now()

    def joint_state_callback(self, msg):
        """Process joint states to compute odometry"""
        try:
            # Debug: Print joint names first time
            if self.prev_left_pos is None:
                self.get_logger().info(f"🔍 Joint names: {msg.name}")
            
            # Find wheel joint indices
            left_indices = []
            right_indices = []
            
            for i, name in enumerate(msg.name):
                if 'left' in name and 'wheel' in name:
                    left_indices.append(i)
                elif 'right' in name and 'wheel' in name:
                    right_indices.append(i)
            
            if not left_indices or not right_indices:
                self.get_logger().warn(f"❌ No wheel joints found! Left: {left_indices}, Right: {right_indices}")
                return
                
            # Debug: Log when we successfully find joints
            if self.prev_left_pos is None:
                self.get_logger().info(f"✅ Found joints - Left indices: {left_indices}, Right indices: {right_indices}")
                
            # Average left and right wheel positions
            left_pos = sum(msg.position[i] for i in left_indices) / len(left_indices)
            right_pos = sum(msg.position[i] for i in right_indices) / len(right_indices)
            
            current_time = self.get_clock().now()
            
            # Initialize previous positions on first run
            if self.prev_left_pos is None or self.prev_right_pos is None:
                self.prev_left_pos = left_pos
                self.prev_right_pos = right_pos
                self.last_odom_time = current_time
                return
            
            # Calculate wheel displacement
            delta_left = left_pos - self.prev_left_pos
            delta_right = right_pos - self.prev_right_pos
            
            # Convert to linear distances
            dist_left = delta_left * self.wheel_radius
            dist_right = delta_right * self.wheel_radius
            
            # Calculate robot motion
            dist_center = (dist_left + dist_right) / 2.0
            delta_theta = (dist_right - dist_left) / self.wheel_separation_y
            
            # Update pose
            if abs(delta_theta) < 1e-6:
                # Straight line motion
                delta_x = dist_center * math.cos(self.theta)
                delta_y = dist_center * math.sin(self.theta)
            else:
                # Arc motion
                radius = dist_center / delta_theta
                delta_x = radius * (math.sin(self.theta + delta_theta) - math.sin(self.theta))
                delta_y = radius * (-math.cos(self.theta + delta_theta) + math.cos(self.theta))
            
            self.x += delta_x
            self.y += delta_y
            self.theta += delta_theta
            
            # Normalize theta
            self.theta = math.atan2(math.sin(self.theta), math.cos(self.theta))
            
            # Calculate velocities
            dt = (current_time - self.last_odom_time).nanoseconds / 1e9
            if dt > 0:
                vx = dist_center / dt
                vy = 0.0  # Assuming non-holonomic
                vth = delta_theta / dt
            else:
                vx = vy = vth = 0.0
            
            # Publish odometry
            self.publish_odometry(current_time, vx, vy, vth)
            
            # Update previous values
            self.prev_left_pos = left_pos
            self.prev_right_pos = right_pos
            self.last_odom_time = current_time
            
            # Debug: Log occasionally
            if int(current_time.nanoseconds / 1e9) % 2 == 0:  # Every 2 seconds
                self.get_logger().info(f"📍 Odom: x={self.x:.3f}, y={self.y:.3f}, θ={self.theta:.3f}")
            
        except Exception as e:
            self.get_logger().error(f"❌ Error processing joint states: {e}")
            import traceback
            self.get_logger().error(f"Traceback: {traceback.format_exc()}")

    def publish_odometry(self, current_time, vx, vy, vth):
        """Publish odometry message and transform"""
        
        # Create odometry message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = 'odom'
        odom.child_frame_id = 'base_link'
        
        # Position
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.position.z = 0.0
        
        # Orientation
        quat = tf_transformations.quaternion_from_euler(0, 0, self.theta)
        odom.pose.pose.orientation.x = quat[0]
        odom.pose.pose.orientation.y = quat[1]
        odom.pose.pose.orientation.z = quat[2]
        odom.pose.pose.orientation.w = quat[3]
        
        # Velocity
        odom.twist.twist.linear.x = vx
        odom.twist.twist.linear.y = vy
        odom.twist.twist.angular.z = vth
        
        # Covariance (simple diagonal matrix)
        odom.pose.covariance[0] = 0.1   # x
        odom.pose.covariance[7] = 0.1   # y
        odom.pose.covariance[35] = 0.1  # theta
        odom.twist.covariance[0] = 0.1  # vx
        odom.twist.covariance[7] = 0.1  # vy
        odom.twist.covariance[35] = 0.1 # vth
        
        # Publish odometry
        self.odom_pub.publish(odom)
        
        # Debug: Confirm publishing
        if int(current_time.nanoseconds / 1e9) % 5 == 0:  # Every 5 seconds
            self.get_logger().info(f"📤 Published odom: x={self.x:.3f}, y={self.y:.3f}")
        
        # Publish transform
        transform = TransformStamped()
        transform.header.stamp = current_time.to_msg()
        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_link'
        
        transform.transform.translation.x = self.x
        transform.transform.translation.y = self.y
        transform.transform.translation.z = 0.0
        
        transform.transform.rotation.x = quat[0]
        transform.transform.rotation.y = quat[1]
        transform.transform.rotation.z = quat[2]
        transform.transform.rotation.w = quat[3]
        
        self.tf_broadcaster.sendTransform(transform)

    def publish_wheel_commands(self):
        now = self.get_clock().now()
        
        # Zero command if timed out
        if (now - self.last_cmd_time) > Duration(seconds=self.cmd_timeout_sec):
            linear_x = 0.0
            angular_z = 0.0
        else:
            linear_x = self.last_cmd_vel.linear.x
            angular_z = self.last_cmd_vel.angular.z
        
        # Skid-steer kinematics
        linear_vel = linear_x / self.wheel_radius
        angular_vel = (angular_z * self.wheel_separation_y / 2.0) / self.wheel_radius
        
        left_wheel_vel = linear_vel - angular_vel
        right_wheel_vel = linear_vel + angular_vel
        
        # Package and publish
        left_msg = Float64MultiArray(data=[left_wheel_vel])
        right_msg = Float64MultiArray(data=[right_wheel_vel])
        
        self.left_front_pub.publish(left_msg)
        self.left_rear_pub.publish(left_msg)
        self.right_front_pub.publish(right_msg)
        self.right_rear_pub.publish(right_msg)

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