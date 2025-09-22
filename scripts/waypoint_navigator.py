#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import ComputePathToPose, FollowPath
from geometry_msgs.msg import PoseWithCovarianceStamped
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