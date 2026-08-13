// generated from rosidl_generator_c/resource/idl__functions.c.em
// with input from synapse_msgs:msg/ServerCommunication.idl
// generated code does not contain a copyright notice
#include "synapse_msgs/msg/detail/server_communication__functions.h"

#include <assert.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>

#include "rcutils/allocator.h"


// Include directives for member types
// Member `msg`
#include "rosidl_runtime_c/string_functions.h"

bool
synapse_msgs__msg__ServerCommunication__init(synapse_msgs__msg__ServerCommunication * msg)
{
  if (!msg) {
    return false;
  }
  // src
  // dest
  // uid
  // ack
  // msg
  if (!rosidl_runtime_c__String__init(&msg->msg)) {
    synapse_msgs__msg__ServerCommunication__fini(msg);
    return false;
  }
  return true;
}

void
synapse_msgs__msg__ServerCommunication__fini(synapse_msgs__msg__ServerCommunication * msg)
{
  if (!msg) {
    return;
  }
  // src
  // dest
  // uid
  // ack
  // msg
  rosidl_runtime_c__String__fini(&msg->msg);
}

bool
synapse_msgs__msg__ServerCommunication__are_equal(const synapse_msgs__msg__ServerCommunication * lhs, const synapse_msgs__msg__ServerCommunication * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  // src
  if (lhs->src != rhs->src) {
    return false;
  }
  // dest
  if (lhs->dest != rhs->dest) {
    return false;
  }
  // uid
  if (lhs->uid != rhs->uid) {
    return false;
  }
  // ack
  if (lhs->ack != rhs->ack) {
    return false;
  }
  // msg
  if (!rosidl_runtime_c__String__are_equal(
      &(lhs->msg), &(rhs->msg)))
  {
    return false;
  }
  return true;
}

bool
synapse_msgs__msg__ServerCommunication__copy(
  const synapse_msgs__msg__ServerCommunication * input,
  synapse_msgs__msg__ServerCommunication * output)
{
  if (!input || !output) {
    return false;
  }
  // src
  output->src = input->src;
  // dest
  output->dest = input->dest;
  // uid
  output->uid = input->uid;
  // ack
  output->ack = input->ack;
  // msg
  if (!rosidl_runtime_c__String__copy(
      &(input->msg), &(output->msg)))
  {
    return false;
  }
  return true;
}

synapse_msgs__msg__ServerCommunication *
synapse_msgs__msg__ServerCommunication__create()
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  synapse_msgs__msg__ServerCommunication * msg = (synapse_msgs__msg__ServerCommunication *)allocator.allocate(sizeof(synapse_msgs__msg__ServerCommunication), allocator.state);
  if (!msg) {
    return NULL;
  }
  memset(msg, 0, sizeof(synapse_msgs__msg__ServerCommunication));
  bool success = synapse_msgs__msg__ServerCommunication__init(msg);
  if (!success) {
    allocator.deallocate(msg, allocator.state);
    return NULL;
  }
  return msg;
}

void
synapse_msgs__msg__ServerCommunication__destroy(synapse_msgs__msg__ServerCommunication * msg)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (msg) {
    synapse_msgs__msg__ServerCommunication__fini(msg);
  }
  allocator.deallocate(msg, allocator.state);
}


bool
synapse_msgs__msg__ServerCommunication__Sequence__init(synapse_msgs__msg__ServerCommunication__Sequence * array, size_t size)
{
  if (!array) {
    return false;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  synapse_msgs__msg__ServerCommunication * data = NULL;

  if (size) {
    data = (synapse_msgs__msg__ServerCommunication *)allocator.zero_allocate(size, sizeof(synapse_msgs__msg__ServerCommunication), allocator.state);
    if (!data) {
      return false;
    }
    // initialize all array elements
    size_t i;
    for (i = 0; i < size; ++i) {
      bool success = synapse_msgs__msg__ServerCommunication__init(&data[i]);
      if (!success) {
        break;
      }
    }
    if (i < size) {
      // if initialization failed finalize the already initialized array elements
      for (; i > 0; --i) {
        synapse_msgs__msg__ServerCommunication__fini(&data[i - 1]);
      }
      allocator.deallocate(data, allocator.state);
      return false;
    }
  }
  array->data = data;
  array->size = size;
  array->capacity = size;
  return true;
}

void
synapse_msgs__msg__ServerCommunication__Sequence__fini(synapse_msgs__msg__ServerCommunication__Sequence * array)
{
  if (!array) {
    return;
  }
  rcutils_allocator_t allocator = rcutils_get_default_allocator();

  if (array->data) {
    // ensure that data and capacity values are consistent
    assert(array->capacity > 0);
    // finalize all array elements
    for (size_t i = 0; i < array->capacity; ++i) {
      synapse_msgs__msg__ServerCommunication__fini(&array->data[i]);
    }
    allocator.deallocate(array->data, allocator.state);
    array->data = NULL;
    array->size = 0;
    array->capacity = 0;
  } else {
    // ensure that data, size, and capacity values are consistent
    assert(0 == array->size);
    assert(0 == array->capacity);
  }
}

synapse_msgs__msg__ServerCommunication__Sequence *
synapse_msgs__msg__ServerCommunication__Sequence__create(size_t size)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  synapse_msgs__msg__ServerCommunication__Sequence * array = (synapse_msgs__msg__ServerCommunication__Sequence *)allocator.allocate(sizeof(synapse_msgs__msg__ServerCommunication__Sequence), allocator.state);
  if (!array) {
    return NULL;
  }
  bool success = synapse_msgs__msg__ServerCommunication__Sequence__init(array, size);
  if (!success) {
    allocator.deallocate(array, allocator.state);
    return NULL;
  }
  return array;
}

void
synapse_msgs__msg__ServerCommunication__Sequence__destroy(synapse_msgs__msg__ServerCommunication__Sequence * array)
{
  rcutils_allocator_t allocator = rcutils_get_default_allocator();
  if (array) {
    synapse_msgs__msg__ServerCommunication__Sequence__fini(array);
  }
  allocator.deallocate(array, allocator.state);
}

bool
synapse_msgs__msg__ServerCommunication__Sequence__are_equal(const synapse_msgs__msg__ServerCommunication__Sequence * lhs, const synapse_msgs__msg__ServerCommunication__Sequence * rhs)
{
  if (!lhs || !rhs) {
    return false;
  }
  if (lhs->size != rhs->size) {
    return false;
  }
  for (size_t i = 0; i < lhs->size; ++i) {
    if (!synapse_msgs__msg__ServerCommunication__are_equal(&(lhs->data[i]), &(rhs->data[i]))) {
      return false;
    }
  }
  return true;
}

bool
synapse_msgs__msg__ServerCommunication__Sequence__copy(
  const synapse_msgs__msg__ServerCommunication__Sequence * input,
  synapse_msgs__msg__ServerCommunication__Sequence * output)
{
  if (!input || !output) {
    return false;
  }
  if (output->capacity < input->size) {
    const size_t allocation_size =
      input->size * sizeof(synapse_msgs__msg__ServerCommunication);
    rcutils_allocator_t allocator = rcutils_get_default_allocator();
    synapse_msgs__msg__ServerCommunication * data =
      (synapse_msgs__msg__ServerCommunication *)allocator.reallocate(
      output->data, allocation_size, allocator.state);
    if (!data) {
      return false;
    }
    // If reallocation succeeded, memory may or may not have been moved
    // to fulfill the allocation request, invalidating output->data.
    output->data = data;
    for (size_t i = output->capacity; i < input->size; ++i) {
      if (!synapse_msgs__msg__ServerCommunication__init(&output->data[i])) {
        // If initialization of any new item fails, roll back
        // all previously initialized items. Existing items
        // in output are to be left unmodified.
        for (; i-- > output->capacity; ) {
          synapse_msgs__msg__ServerCommunication__fini(&output->data[i]);
        }
        return false;
      }
    }
    output->capacity = input->size;
  }
  output->size = input->size;
  for (size_t i = 0; i < input->size; ++i) {
    if (!synapse_msgs__msg__ServerCommunication__copy(
        &(input->data[i]), &(output->data[i])))
    {
      return false;
    }
  }
  return true;
}
