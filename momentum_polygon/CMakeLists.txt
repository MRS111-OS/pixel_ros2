cmake_minimum_required(VERSION 3.5)
project(momentum_polygon)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "action/RecordPolygon.action"
  DEPENDENCIES geometry_msgs
)

# add_executable(polygon_recorder_server src/polygon_recorder_server.cpp)

install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  src/polygon_recorder_server.py
  src/polygon_manager_node.py
  src/cover_area.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
