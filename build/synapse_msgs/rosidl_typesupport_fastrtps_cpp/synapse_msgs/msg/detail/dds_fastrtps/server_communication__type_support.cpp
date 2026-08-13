// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__type_support.cpp.em
// with input from synapse_msgs:msg/ServerCommunication.idl
// generated code does not contain a copyright notice
#include "synapse_msgs/msg/detail/server_communication__rosidl_typesupport_fastrtps_cpp.hpp"
#include "synapse_msgs/msg/detail/server_communication__struct.hpp"

#include <limits>
#include <stdexcept>
#include <string>
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_fastrtps_cpp/identifier.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_fastrtps_cpp/wstring_conversion.hpp"
#include "fastcdr/Cdr.h"


// forward declaration of message dependencies and their conversion functions

namespace synapse_msgs
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_synapse_msgs
cdr_serialize(
  const synapse_msgs::msg::ServerCommunication & ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  // Member: src
  cdr << ros_message.src;
  // Member: dest
  cdr << ros_message.dest;
  // Member: uid
  cdr << ros_message.uid;
  // Member: ack
  cdr << ros_message.ack;
  // Member: msg
  cdr << ros_message.msg;
  return true;
}

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_synapse_msgs
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  synapse_msgs::msg::ServerCommunication & ros_message)
{
  // Member: src
  cdr >> ros_message.src;

  // Member: dest
  cdr >> ros_message.dest;

  // Member: uid
  cdr >> ros_message.uid;

  // Member: ack
  cdr >> ros_message.ack;

  // Member: msg
  cdr >> ros_message.msg;

  return true;
}  // NOLINT(readability/fn_size)

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_synapse_msgs
get_serialized_size(
  const synapse_msgs::msg::ServerCommunication & ros_message,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // Member: src
  {
    size_t item_size = sizeof(ros_message.src);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: dest
  {
    size_t item_size = sizeof(ros_message.dest);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: uid
  {
    size_t item_size = sizeof(ros_message.uid);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: ack
  {
    size_t item_size = sizeof(ros_message.ack);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // Member: msg
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message.msg.size() + 1);

  return current_alignment - initial_alignment;
}

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_synapse_msgs
max_serialized_size_ServerCommunication(
  bool & full_bounded,
  bool & is_plain,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  size_t last_member_size = 0;
  (void)last_member_size;
  (void)padding;
  (void)wchar_size;

  full_bounded = true;
  is_plain = true;


  // Member: src
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: dest
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: uid
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: ack
  {
    size_t array_size = 1;

    last_member_size = array_size * sizeof(uint8_t);
    current_alignment += array_size * sizeof(uint8_t);
  }

  // Member: msg
  {
    size_t array_size = 1;

    full_bounded = false;
    is_plain = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }

  size_t ret_val = current_alignment - initial_alignment;
  if (is_plain) {
    // All members are plain, and type is not empty.
    // We still need to check that the in-memory alignment
    // is the same as the CDR mandated alignment.
    using DataType = synapse_msgs::msg::ServerCommunication;
    is_plain =
      (
      offsetof(DataType, msg) +
      last_member_size
      ) == ret_val;
  }

  return ret_val;
}

static bool _ServerCommunication__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  auto typed_message =
    static_cast<const synapse_msgs::msg::ServerCommunication *>(
    untyped_ros_message);
  return cdr_serialize(*typed_message, cdr);
}

static bool _ServerCommunication__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  auto typed_message =
    static_cast<synapse_msgs::msg::ServerCommunication *>(
    untyped_ros_message);
  return cdr_deserialize(cdr, *typed_message);
}

static uint32_t _ServerCommunication__get_serialized_size(
  const void * untyped_ros_message)
{
  auto typed_message =
    static_cast<const synapse_msgs::msg::ServerCommunication *>(
    untyped_ros_message);
  return static_cast<uint32_t>(get_serialized_size(*typed_message, 0));
}

static size_t _ServerCommunication__max_serialized_size(char & bounds_info)
{
  bool full_bounded;
  bool is_plain;
  size_t ret_val;

  ret_val = max_serialized_size_ServerCommunication(full_bounded, is_plain, 0);

  bounds_info =
    is_plain ? ROSIDL_TYPESUPPORT_FASTRTPS_PLAIN_TYPE :
    full_bounded ? ROSIDL_TYPESUPPORT_FASTRTPS_BOUNDED_TYPE : ROSIDL_TYPESUPPORT_FASTRTPS_UNBOUNDED_TYPE;
  return ret_val;
}

static message_type_support_callbacks_t _ServerCommunication__callbacks = {
  "synapse_msgs::msg",
  "ServerCommunication",
  _ServerCommunication__cdr_serialize,
  _ServerCommunication__cdr_deserialize,
  _ServerCommunication__get_serialized_size,
  _ServerCommunication__max_serialized_size
};

static rosidl_message_type_support_t _ServerCommunication__handle = {
  rosidl_typesupport_fastrtps_cpp::typesupport_identifier,
  &_ServerCommunication__callbacks,
  get_message_typesupport_handle_function,
};

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace synapse_msgs

namespace rosidl_typesupport_fastrtps_cpp
{

template<>
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_EXPORT_synapse_msgs
const rosidl_message_type_support_t *
get_message_type_support_handle<synapse_msgs::msg::ServerCommunication>()
{
  return &synapse_msgs::msg::typesupport_fastrtps_cpp::_ServerCommunication__handle;
}

}  // namespace rosidl_typesupport_fastrtps_cpp

#ifdef __cplusplus
extern "C"
{
#endif

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, synapse_msgs, msg, ServerCommunication)() {
  return &synapse_msgs::msg::typesupport_fastrtps_cpp::_ServerCommunication__handle;
}

#ifdef __cplusplus
}
#endif
