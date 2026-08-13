// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from synapse_msgs:msg/ServerCommunication.idl
// generated code does not contain a copyright notice

#ifndef SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__STRUCT_H_
#define SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'msg'
#include "rosidl_runtime_c/string.h"

/// Struct defined in msg/ServerCommunication in the package synapse_msgs.
typedef struct synapse_msgs__msg__ServerCommunication
{
  /// ID for the source component (Buggy-1, Server-2)
  uint8_t src;
  /// ID for the destination component (Buggy-1, Server-2)
  uint8_t dest;
  /// Message ID / Unique identifier counter (Different Base counter for Buggy and Server)
  uint8_t uid;
  /// Status field (0 for Blank, 1 for Ack)
  uint8_t ack;
  /// Variable-length byte array for the payload string
  rosidl_runtime_c__String msg;
} synapse_msgs__msg__ServerCommunication;

// Struct for a sequence of synapse_msgs__msg__ServerCommunication.
typedef struct synapse_msgs__msg__ServerCommunication__Sequence
{
  synapse_msgs__msg__ServerCommunication * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} synapse_msgs__msg__ServerCommunication__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // SYNAPSE_MSGS__MSG__DETAIL__SERVER_COMMUNICATION__STRUCT_H_
