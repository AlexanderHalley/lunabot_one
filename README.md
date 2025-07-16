lunabot sim V1
to launch you colcon build then source the workspace and then use the launch sim file
Then to control with keyboard run this in another terminal: 

ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/diff_cont/cmd_vel_unstamped

Also you can then run rviz2
Use Jazzy