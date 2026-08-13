# generated from rosidl_cmake/cmake/rosidl_cmake_aggregate_target-extras.cmake.in

# Create a convenience aggregate target synapse_msgs::synapse_msgs
# that links all generated interface targets, so downstream packages can use
# a single modern CMake target name instead of ${synapse_msgs_TARGETS}.
if(synapse_msgs_TARGETS AND NOT TARGET synapse_msgs::synapse_msgs)
  add_library(synapse_msgs::synapse_msgs INTERFACE IMPORTED)
  set_target_properties(synapse_msgs::synapse_msgs PROPERTIES
    INTERFACE_LINK_LIBRARIES "${synapse_msgs_TARGETS}")
endif()
