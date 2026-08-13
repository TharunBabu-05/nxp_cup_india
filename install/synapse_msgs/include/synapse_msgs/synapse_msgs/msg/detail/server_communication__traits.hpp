// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from synapse_msgs:msg/ServerCommunication.idl
// generated code does not contain a copyright notice

#ifndef SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__TRAITS_HPP_
#define SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__TRAITS_HPP_

#include <stdint.h>

#include <sstream>
#include <string>
#include <type_traits>

#include "synapse_msgs/msg/detail/server_communication__struct.hpp"
#include "rosidl_runtime_cpp/traits.hpp"

namespace synapse_msgs
{

namespace msg
{

inline void to_flow_style_yaml(
  const ServerCommunication & msg,
  std::ostream & out)
{
  out << "{";
  // member: src
  {
    out << "src: ";
    rosidl_generator_traits::value_to_yaml(msg.src, out);
    out << ", ";
  }

  // member: dest
  {
    out << "dest: ";
    rosidl_generator_traits::value_to_yaml(msg.dest, out);
    out << ", ";
  }

  // member: uid
  {
    out << "uid: ";
    rosidl_generator_traits::value_to_yaml(msg.uid, out);
    out << ", ";
  }

  // member: ack
  {
    out << "ack: ";
    rosidl_generator_traits::value_to_yaml(msg.ack, out);
    out << ", ";
  }

  // member: msg
  {
    out << "msg: ";
    rosidl_generator_traits::value_to_yaml(msg.msg, out);
  }
  out << "}";
}  // NOLINT(readability/fn_size)

inline void to_block_style_yaml(
  const ServerCommunication & msg,
  std::ostream & out, size_t indentation = 0)
{
  // member: src
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "src: ";
    rosidl_generator_traits::value_to_yaml(msg.src, out);
    out << "\n";
  }

  // member: dest
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "dest: ";
    rosidl_generator_traits::value_to_yaml(msg.dest, out);
    out << "\n";
  }

  // member: uid
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "uid: ";
    rosidl_generator_traits::value_to_yaml(msg.uid, out);
    out << "\n";
  }

  // member: ack
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "ack: ";
    rosidl_generator_traits::value_to_yaml(msg.ack, out);
    out << "\n";
  }

  // member: msg
  {
    if (indentation > 0) {
      out << std::string(indentation, ' ');
    }
    out << "msg: ";
    rosidl_generator_traits::value_to_yaml(msg.msg, out);
    out << "\n";
  }
}  // NOLINT(readability/fn_size)

inline std::string to_yaml(const ServerCommunication & msg, bool use_flow_style = false)
{
  std::ostringstream out;
  if (use_flow_style) {
    to_flow_style_yaml(msg, out);
  } else {
    to_block_style_yaml(msg, out);
  }
  return out.str();
}

}  // namespace msg

}  // namespace synapse_msgs

namespace rosidl_generator_traits
{

[[deprecated("use synapse_msgs::msg::to_block_style_yaml() instead")]]
inline void to_yaml(
  const synapse_msgs::msg::ServerCommunication & msg,
  std::ostream & out, size_t indentation = 0)
{
  synapse_msgs::msg::to_block_style_yaml(msg, out, indentation);
}

[[deprecated("use synapse_msgs::msg::to_yaml() instead")]]
inline std::string to_yaml(const synapse_msgs::msg::ServerCommunication & msg)
{
  return synapse_msgs::msg::to_yaml(msg);
}

template<>
inline const char * data_type<synapse_msgs::msg::ServerCommunication>()
{
  return "synapse_msgs::msg::ServerCommunication";
}

template<>
inline const char * name<synapse_msgs::msg::ServerCommunication>()
{
  return "synapse_msgs/msg/ServerCommunication";
}

template<>
struct has_fixed_size<synapse_msgs::msg::ServerCommunication>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<synapse_msgs::msg::ServerCommunication>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<synapse_msgs::msg::ServerCommunication>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__TRAITS_HPP_
