#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from nav2_msgs.action import ComputePathToPose, FollowPath
import sys

class SimpleNavigator(Node):
    def __init__(self):
        super().__init__('simple_navigator')
        
        self.compute_path_client = ActionClient(self, ComputePathToPose, '/compute_path_to_pose')
        self.follow_path_client = ActionClient(self, FollowPath, '/follow_path')
        
    def navigate_to_pose(self, x, y, yaw=0.0):
        # Convert yaw to quaternion
        import math
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
        
        self.get_logger().info(f'Computing path to ({x}, {y}, {yaw})')
        
        self.compute_path_client.wait_for_server()
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
            self.get_logger().error('No path found')
            return False
            
        self.get_logger().info(f'Path computed with {len(result.path.poses)} waypoints')
        
        # Step 2: Follow path
        follow_goal = FollowPath.Goal()
        follow_goal.path = result.path
        
        self.get_logger().info('Following path...')
        
        self.follow_path_client.wait_for_server()
        follow_future = self.follow_path_client.send_goal_async(follow_goal)
        rclpy.spin_until_future_complete(self, follow_future)
        
        follow_handle = follow_future.result()
        if not follow_handle.accepted:
            self.get_logger().error('Path following goal rejected')
            return False
            
        follow_result_future = follow_handle.get_result_async()
        rclpy.spin_until_future_complete(self, follow_result_future)
        
        self.get_logger().info('Navigation completed!')
        return True

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 navigate_to_goal.py <x> <y> [yaw_angle]")
        print("Example: python3 navigate_to_goal.py 3.34933 1.52105 1.11345")
        return
        
    x = float(sys.argv[1])
    y = float(sys.argv[2])
    yaw = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    
    rclpy.init()
    navigator = SimpleNavigator()
    
    try:
        navigator.navigate_to_pose(x, y, yaw)
    except KeyboardInterrupt:
        pass
    finally:
        navigator.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()