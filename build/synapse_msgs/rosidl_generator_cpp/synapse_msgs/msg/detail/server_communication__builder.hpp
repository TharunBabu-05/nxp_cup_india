// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from synapse_msgs:msg/ServerCommunication.idl
// generated code does not contain a copyright notice

#ifndef SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__BUILDER_HPP_
#define SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "synapse_msgs/msg/detail/server_communication__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace synapse_msgs
{

namespace msg
{

namespace builder
{

class Init_ServerCommunication_msg
{
public:
  explicit Init_ServerCommunication_msg(::synapse_msgs::msg::ServerCommunication & msg)
  : msg_(msg)
  {}
  ::synapse_msgs::msg::ServerCommunication msg(::synapse_msgs::msg::ServerCommunication::_msg_type arg)
  {
    msg_.msg = std::move(arg);
    return std::move(msg_);
  }

private:
  ::synapse_msgs::msg::ServerCommunication msg_;
};

class Init_ServerCommunication_ack
{
public:
  explicit Init_ServerCommunication_ack(::synapse_msgs::msg::ServerCommunication & msg)
  : msg_(msg)
  {}
  Init_ServerCommunication_msg ack(::synapse_msgs::msg::ServerCommunication::_ack_type arg)
  {
    msg_.ack = std::move(arg);
    return Init_ServerCommunication_msg(msg_);
  }

private:
  ::synapse_msgs::msg::ServerCommunication msg_;
};

class Init_ServerCommunication_uid
{
public:
  explicit Init_ServerCommunication_uid(::synapse_msgs::msg::ServerCommunication & msg)
  : msg_(msg)
  {}
  Init_ServerCommunication_ack uid(::synapse_msgs::msg::ServerCommunication::_uid_type arg)
  {
    msg_.uid = std::move(arg);
    return Init_ServerCommunication_ack(msg_);
  }

private:
  ::synapse_msgs::msg::ServerCommunication msg_;
};

class Init_ServerCommunication_dest
{
public:
  explicit Init_ServerCommunication_dest(::synapse_msgs::msg::ServerCommunication & msg)
  : msg_(msg)
  {}
  Init_ServerCommunication_uid dest(::synapse_msgs::msg::ServerCommunication::_dest_type arg)
  {
    msg_.dest = std::move(arg);
    return Init_ServerCommunication_uid(msg_);
  }

private:
  ::synapse_msgs::msg::ServerCommunication msg_;
};

class Init_ServerCommunication_src
{
public:
  Init_ServerCommunication_src()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ServerCommunication_dest src(::synapse_msgs::msg::ServerCommunication::_src_type arg)
  {
    msg_.src = std::move(arg);
    return Init_ServerCommunication_dest(msg_);
  }

private:
  ::synapse_msgs::msg::ServerCommunication msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::synapse_msgs::msg::ServerCommunication>()
{
  return synapse_msgs::msg::builder::Init_ServerCommunication_src();
}

}  // namespace synapse_msgs

#endif  // SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__BUILDER_HPP_
