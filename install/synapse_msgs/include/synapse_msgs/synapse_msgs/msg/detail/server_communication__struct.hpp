// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from synapse_msgs:msg/ServerCommunication.idl
// generated code does not contain a copyright notice

#ifndef SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__STRUCT_HPP_
#define SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__STRUCT_HPP_

#include <algorithm>
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>

#include "rosidl_runtime_cpp/bounded_vector.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


#ifndef _WIN32
# define DEPRECATED__synapse_msgs__msg__ServerCommunication __attribute__((deprecated))
#else
# define DEPRECATED__synapse_msgs__msg__ServerCommunication __declspec(deprecated)
#endif

namespace synapse_msgs
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ServerCommunication_
{
  using Type = ServerCommunication_<ContainerAllocator>;

  explicit ServerCommunication_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->src = 0;
      this->dest = 0;
      this->uid = 0;
      this->ack = 0;
      this->msg = "";
    }
  }

  explicit ServerCommunication_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : msg(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->src = 0;
      this->dest = 0;
      this->uid = 0;
      this->ack = 0;
      this->msg = "";
    }
  }

  // field types and members
  using _src_type =
    uint8_t;
  _src_type src;
  using _dest_type =
    uint8_t;
  _dest_type dest;
  using _uid_type =
    uint8_t;
  _uid_type uid;
  using _ack_type =
    uint8_t;
  _ack_type ack;
  using _msg_type =
    std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>>;
  _msg_type msg;

  // setters for named parameter idiom
  Type & set__src(
    const uint8_t & _arg)
  {
    this->src = _arg;
    return *this;
  }
  Type & set__dest(
    const uint8_t & _arg)
  {
    this->dest = _arg;
    return *this;
  }
  Type & set__uid(
    const uint8_t & _arg)
  {
    this->uid = _arg;
    return *this;
  }
  Type & set__ack(
    const uint8_t & _arg)
  {
    this->ack = _arg;
    return *this;
  }
  Type & set__msg(
    const std::basic_string<char, std::char_traits<char>, typename std::allocator_traits<ContainerAllocator>::template rebind_alloc<char>> & _arg)
  {
    this->msg = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    synapse_msgs::msg::ServerCommunication_<ContainerAllocator> *;
  using ConstRawPtr =
    const synapse_msgs::msg::ServerCommunication_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<synapse_msgs::msg::ServerCommunication_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<synapse_msgs::msg::ServerCommunication_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      synapse_msgs::msg::ServerCommunication_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<synapse_msgs::msg::ServerCommunication_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      synapse_msgs::msg::ServerCommunication_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<synapse_msgs::msg::ServerCommunication_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<synapse_msgs::msg::ServerCommunication_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<synapse_msgs::msg::ServerCommunication_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__synapse_msgs__msg__ServerCommunication
    std::shared_ptr<synapse_msgs::msg::ServerCommunication_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__synapse_msgs__msg__ServerCommunication
    std::shared_ptr<synapse_msgs::msg::ServerCommunication_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ServerCommunication_ & other) const
  {
    if (this->src != other.src) {
      return false;
    }
    if (this->dest != other.dest) {
      return false;
    }
    if (this->uid != other.uid) {
      return false;
    }
    if (this->ack != other.ack) {
      return false;
    }
    if (this->msg != other.msg) {
      return false;
    }
    return true;
  }
  bool operator!=(const ServerCommunication_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ServerCommunication_

// alias to use template instance with default allocator
using ServerCommunication =
  synapse_msgs::msg::ServerCommunication_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace synapse_msgs

#endif  // SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__STRUCT_HPP_
