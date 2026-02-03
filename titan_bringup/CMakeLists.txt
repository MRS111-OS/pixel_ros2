################################################################################
# Set minimum required version of cmake, project name and compile options
################################################################################
cmake_minimum_required(VERSION 3.5)
project(titan_bringup)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

################################################################################
# Find ament packages and libraries for ament and system dependencies
################################################################################
find_package(ament_cmake REQUIRED)

################################################################################
# Install
################################################################################
install(
  DIRECTORY launch param script
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  script/odom_to_base.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  PROGRAMS
    script/cover_area.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME cover_area
)

################################################################################
# Macro for ament package
################################################################################
ament_package()
