#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import ComputePathToPose, FollowPath
from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformListener, Buffer
from tf2_ros import LookupException, ConnectivityException, ExtrapolationException
import math
import time

class WaypointNavigator(Node):
    def __init__(self, waypoint_pause_duration=2.0):
        super().__init__('waypoint_navigator')

        # Configuration
        self.waypoint_pause_duration = waypoint_pause_duration
        
        self.compute_path_client = ActionClient(self, ComputePathToPose, '/compute_path_to_pose')
        self.follow_path_client = ActionClient(self, FollowPath, '/follow_path')
        
        # Publishers
        self.initial_pose_pub = self.create_publisher(
            PoseWithCovarianceStamped,
            '/initialpose',
            10
        )

        # Subscribers for position tracking
        self.odom_sub = self.create_subscription(
            Odometry,
            '/odom',
            self.odom_callback,
            10
        )

        # TF2 buffer and listener for transform tracking
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Current position storage
        self.current_odom_pose = None
        
        # Wait for action servers
        self.get_logger().info('Waiting for navigation action servers...')
        self.compute_path_client.wait_for_server(timeout_sec=10.0)
        self.follow_path_client.wait_for_server(timeout_sec=10.0)
        self.get_logger().info('Navigation action servers ready!')
        
    def set_initial_pose(self, x=0.0, y=0.0, yaw=0.0):
        """Set the initial pose of the robot on the map"""
        pose_msg = PoseWithCovarianceStamped()
        pose_msg.header.frame_id = "map"
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        
        # Position
        pose_msg.pose.pose.position.x = x
        pose_msg.pose.pose.position.y = y
        pose_msg.pose.pose.position.z = 0.0
        
        # Orientation (convert yaw to quaternion)
        qw = math.cos(yaw / 2.0)
        qz = math.sin(yaw / 2.0)
        pose_msg.pose.pose.orientation.x = 0.0
        pose_msg.pose.pose.orientation.y = 0.0
        pose_msg.pose.pose.orientation.z = qz
        pose_msg.pose.pose.orientation.w = qw
        
        # Covariance matrix (simplified)
        pose_msg.pose.covariance = [0.0] * 36
        pose_msg.pose.covariance[0] = 0.25   # x variance
        pose_msg.pose.covariance[7] = 0.25   # y variance  
        pose_msg.pose.covariance[35] = 0.06853892326654787  # yaw variance
        
        self.initial_pose_pub.publish(pose_msg)
        self.get_logger().info(f'Set initial pose: ({x}, {y}, {yaw})')

    def odom_callback(self, msg):
        """Store current odometry pose"""
        self.current_odom_pose = msg.pose.pose

    def get_robot_transform_pose(self, target_frame='map', source_frame='base_link'):
        """Get robot pose from tf2 transforms"""
        try:
            # Get the transform from map to base_link
            transform = self.tf_buffer.lookup_transform(
                target_frame,
                source_frame,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=1.0)
            )

            # Create a pose from the transform
            pose = type('Pose', (), {})()
            pose.position = transform.transform.translation
            pose.orientation = transform.transform.rotation
            return pose

        except (LookupException, ConnectivityException, ExtrapolationException) as e:
            self.get_logger().debug(f'Could not get transform from {source_frame} to {target_frame}: {e}')
            return None

    def publish_position_verification(self, target_x, target_y, target_yaw, waypoint_num):
        """Publish position verification information when reaching a waypoint"""
        def quaternion_to_yaw(quat):
            """Convert quaternion to yaw angle"""
            siny_cosp = 2 * (quat.w * quat.z + quat.x * quat.y)
            cosy_cosp = 1 - 2 * (quat.y * quat.y + quat.z * quat.z)
            return math.atan2(siny_cosp, cosy_cosp)

        self.get_logger().info("=" * 60)
        self.get_logger().info(f"WAYPOINT {waypoint_num} ARRIVAL VERIFICATION")
        self.get_logger().info("=" * 60)

        # Target position
        self.get_logger().info(f"Target Position: ({target_x:.3f}, {target_y:.3f}, {target_yaw:.3f})")

        # Odometry position (navigation system's view)
        if self.current_odom_pose:
            odom_x = self.current_odom_pose.position.x
            odom_y = self.current_odom_pose.position.y
            odom_yaw = quaternion_to_yaw(self.current_odom_pose.orientation)

            odom_error_x = abs(odom_x - target_x)
            odom_error_y = abs(odom_y - target_y)
            odom_error_distance = math.sqrt(odom_error_x**2 + odom_error_y**2)
            odom_error_yaw = abs(odom_yaw - target_yaw)

            self.get_logger().info(f"Odometry Position: ({odom_x:.3f}, {odom_y:.3f}, {odom_yaw:.3f})")
            self.get_logger().info(f"Odometry Error: dist={odom_error_distance:.3f}m, yaw={odom_error_yaw:.3f}rad")

        # Transform position (map frame localization result)
        tf_pose = self.get_robot_transform_pose('map', 'base_link')
        if tf_pose:
            tf_x = tf_pose.position.x
            tf_y = tf_pose.position.y
            tf_yaw = quaternion_to_yaw(tf_pose.orientation)

            tf_error_x = abs(tf_x - target_x)
            tf_error_y = abs(tf_y - target_y)
            tf_error_distance = math.sqrt(tf_error_x**2 + tf_error_y**2)
            tf_error_yaw = abs(tf_yaw - target_yaw)

            self.get_logger().info(f"Map→base_link Transform: ({tf_x:.3f}, {tf_y:.3f}, {tf_yaw:.3f})")
            self.get_logger().info(f"Transform Error: dist={tf_error_distance:.3f}m, yaw={tf_error_yaw:.3f}rad")

            # Compare odometry vs Transform (drift analysis)
            if self.current_odom_pose:
                drift_x = abs(odom_x - tf_x)
                drift_y = abs(odom_y - tf_y)
                drift_distance = math.sqrt(drift_x**2 + drift_y**2)
                drift_yaw = abs(odom_yaw - tf_yaw)

                self.get_logger().info(f"Odometry vs Transform Drift: dist={drift_distance:.3f}m, yaw={drift_yaw:.3f}rad")

        # Also check odom frame position for comparison
        odom_tf_pose = self.get_robot_transform_pose('odom', 'base_link')
        if odom_tf_pose:
            odom_tf_x = odom_tf_pose.position.x
            odom_tf_y = odom_tf_pose.position.y
            odom_tf_yaw = quaternion_to_yaw(odom_tf_pose.orientation)
            self.get_logger().info(f"Odom→base_link Transform: ({odom_tf_x:.3f}, {odom_tf_y:.3f}, {odom_tf_yaw:.3f})")

        self.get_logger().info("=" * 60)
        
    def navigate_to_pose(self, x, y, yaw=0.0):
        """Navigate to a single waypoint"""
        # Convert yaw to quaternion
        qw = math.cos(yaw / 2.0)
        qz = math.sin(yaw / 2.0)
        
        # Step 1: Compute path
        goal_msg = ComputePathToPose.Goal()
        goal_msg.goal.header.frame_id = "map"
        goal_msg.goal.pose.position.x = x
        goal_msg.goal.pose.position.y = y
        goal_msg.goal.pose.position.z = 0.0
        goal_msg.goal.pose.orientation.x = 0.0
        goal_msg.goal.pose.orientation.y = 0.0
        goal_msg.goal.pose.orientation.z = qz
        goal_msg.goal.pose.orientation.w = qw
        goal_msg.planner_id = ""
        goal_msg.use_start = False
        
        self.get_logger().info(f'Computing path to waypoint ({x:.2f}, {y:.2f}, {yaw:.2f})')
        
        future = self.compute_path_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, future)
        
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Path planning goal rejected')
            return False
            
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        
        result = result_future.result().result
        if not result.path.poses:
            self.get_logger().error('No path found to waypoint')
            return False
            
        self.get_logger().info(f'Path computed with {len(result.path.poses)} poses')
        
        # Step 2: Follow path
        follow_goal = FollowPath.Goal()
        follow_goal.path = result.path
        
        self.get_logger().info('Following path to waypoint...')
        
        follow_future = self.follow_path_client.send_goal_async(follow_goal)
        rclpy.spin_until_future_complete(self, follow_future)
        
        follow_handle = follow_future.result()
        if not follow_handle.accepted:
            self.get_logger().error('Path following goal rejected')
            return False
            
        follow_result_future = follow_handle.get_result_async()
        rclpy.spin_until_future_complete(self, follow_result_future)
        
        self.get_logger().info('Arrived at waypoint!')
        return True
        
    def navigate_waypoints(self, waypoints, set_initial_pose=True):
        """
        Navigate through a list of waypoints sequentially
        
        Args:
            waypoints: List of tuples (x, y) or (x, y, yaw)
            set_initial_pose: If True, set initial pose to (0,0,0)
        """
        if set_initial_pose:
            self.get_logger().info('Setting initial pose to origin (0, 0, 0)')
            self.set_initial_pose(0.0, 0.0, 0.0)
            time.sleep(2.0)  # Give AMCL time to initialize
            
        self.get_logger().info(f'Starting waypoint navigation with {len(waypoints)} waypoints')
        
        for i, waypoint in enumerate(waypoints):
            self.get_logger().info(f'--- Waypoint {i+1}/{len(waypoints)} ---')
            
            # Handle both (x, y) and (x, y, yaw) formats
            if len(waypoint) == 2:
                x, y = waypoint
                yaw = 0.0
            elif len(waypoint) == 3:
                x, y, yaw = waypoint
            else:
                self.get_logger().error(f'Invalid waypoint format: {waypoint}')
                continue
                
            success = self.navigate_to_pose(x, y, yaw)
            
            if not success:
                self.get_logger().error(f'Failed to reach waypoint {i+1}: ({x}, {y}, {yaw})')
                return False

            self.get_logger().info(f'Successfully reached waypoint {i+1}')

            # Publish position verification
            self.publish_position_verification(x, y, yaw, i+1)

            # Pause at waypoint (configurable duration)
            if self.waypoint_pause_duration > 0:
                self.get_logger().info(f'Pausing for {self.waypoint_pause_duration} seconds at waypoint...')
                time.sleep(self.waypoint_pause_duration)
            
        self.get_logger().info('All waypoints completed successfully!')
        return True

def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python3 waypoint_navigator.py x1 y1 [yaw1] x2 y2 [yaw2] ...")
        print("  ")
        print("Examples:")
        print("  # Simple rectangular path")
        print("  python3 waypoint_navigator.py 2.0 0.0 2.0 2.0 0.0 2.0 0.0 0.0")
        print("  ")
        print("  # With orientations")  
        print("  python3 waypoint_navigator.py 2.0 0.0 1.57 2.0 2.0 3.14 0.0 2.0 -1.57 0.0 0.0 0.0")
        return
        
    # Parse waypoints from command line
    waypoints = []
    i = 1
    while i < len(sys.argv):
        if i + 1 < len(sys.argv):
            x = float(sys.argv[i])
            y = float(sys.argv[i + 1])
            
            # Check if there's a yaw value
            if i + 2 < len(sys.argv):
                try:
                    yaw = float(sys.argv[i + 2])
                    waypoints.append((x, y, yaw))
                    i += 3
                except ValueError:
                    waypoints.append((x, y))
                    i += 2
            else:
                waypoints.append((x, y))
                i += 2
        else:
            break
            
    if not waypoints:
        print("Error: No valid waypoints parsed")
        return
        
    print(f"Parsed waypoints: {waypoints}")
    
    rclpy.init()
    navigator = WaypointNavigator(waypoint_pause_duration=2.0)  # 2 seconds pause at each waypoint
    
    try:
        navigator.navigate_waypoints(waypoints, set_initial_pose=True)
    except KeyboardInterrupt:
        navigator.get_logger().info('Navigation interrupted by user')
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()