cmake_minimum_required(VERSION 3.5)
project(lunabot_one)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++17 (required for sparkcan)
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)

# Find sparkcan library (installed system-wide, not a ROS2 package)
set(CMAKE_PREFIX_PATH "/usr/local/lib/cmake/sparkcan;${CMAKE_PREFIX_PATH}")
find_package(sparkcan REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # uncomment the line when a copyright and license is not present in all source files
  #set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # uncomment the line when this package is not in a git repo
  #set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# Build SparkFlex driver node
add_executable(sparkflex_driver_node src/sparkflex_driver_node.cpp)
ament_target_dependencies(sparkflex_driver_node
  rclcpp
  geometry_msgs
  nav_msgs
  sensor_msgs
  tf2
  tf2_geometry_msgs
)
target_link_libraries(sparkflex_driver_node sparkcan::sparkcan)

# Install C++ executables
install(TARGETS
  sparkflex_driver_node
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY config description launch worlds maps scripts hardware
  DESTINATION share/${PROJECT_NAME}
)
# install python scripts
install(PROGRAMS
  nodes/lunabot_joy_teleop.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME lunabot_joy_teleop
)

install(PROGRAMS
  nodes/twist_to_stamped_relay.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME twist_to_stamped_relay
)

install(PROGRAMS
  nodes/turning_diagnostics.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME turning_diagnostics
)

install(PROGRAMS
  scripts/initial_pose_setter.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME initial_pose_setter
)

install(PROGRAMS
  nodes/lidar_merger.py
  DESTINATION lib/${PROJECT_NAME}
)

install(PROGRAMS
  nodes/zone_detector.py
  DESTINATION lib/${PROJECT_NAME}
)



ament_package()
