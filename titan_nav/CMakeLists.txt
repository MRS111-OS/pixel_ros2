cmake_minimum_required(VERSION 3.8)
project(titan_nav)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(nav_msgs REQUIRED)


install(
  DIRECTORY launch urdf config models worlds maps rviz
  DESTINATION share/${PROJECT_NAME}
)



add_executable(planner_metric_node src/planner_metric_node.cpp)



install(TARGETS
  planner_metric_node
  DESTINATION lib/${PROJECT_NAME}
)
ament_target_dependencies(planner_metric_node
  rclcpp
  nav_msgs
)




if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  # the following line skips the linter which checks for copyrights
  # comment the line when a copyright and license is added to all source files
  set(ament_cmake_copyright_FOUND TRUE)
  # the following line skips cpplint (only works in a git repo)
  # comment the line when this package is in a git repo and when
  # a copyright and license is added to all source files
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
