cmake_minimum_required(VERSION 3.8)
project(rzv_demo_dexhand)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

# Install launch files
install(DIRECTORY
  launch
  DESTINATION share/${PROJECT_NAME}/
)

# Install config files
install(DIRECTORY
  config
  DESTINATION share/${PROJECT_NAME}/
)

# Install setup files
install(PROGRAMS
  setup/ruiyan_rh2_init.sh
  setup/inspire_rh56_init.sh
  DESTINATION share/${PROJECT_NAME}/setup
)

ament_package()
