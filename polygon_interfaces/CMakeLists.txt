cmake_minimum_required(VERSION 3.8)
project(polygon_interfaces)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(geometry_msgs REQUIRED)

# Generate interfaces
rosidl_generate_interfaces(${PROJECT_NAME}

  "action/RecordPolygon.action"

  "srv/ListPolygons.srv"
  "srv/GetPolygon.srv"

  DEPENDENCIES
  geometry_msgs
)

# Export runtime dependencies
ament_export_dependencies(
  rosidl_default_runtime
)

ament_package()