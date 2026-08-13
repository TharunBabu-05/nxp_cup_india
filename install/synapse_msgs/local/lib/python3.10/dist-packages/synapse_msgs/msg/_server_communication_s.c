// generated from rosidl_generator_py/resource/_idl_support.c.em
// with input from synapse_msgs:msg/ServerCommunication.idl
// generated code does not contain a copyright notice
#define NPY_NO_DEPRECATED_API NPY_1_7_API_VERSION
#include <Python.h>
#include <stdbool.h>
#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-function"
#endif
#include "numpy/ndarrayobject.h"
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif
#include "rosidl_runtime_c/visibility_control.h"
#include "synapse_msgs/msg/detail/server_communication__struct.h"
#include "synapse_msgs/msg/detail/server_communication__functions.h"

#include "rosidl_runtime_c/string.h"
#include "rosidl_runtime_c/string_functions.h"


ROSIDL_GENERATOR_C_EXPORT
bool synapse_msgs__msg__server_communication__convert_from_py(PyObject * _pymsg, void * _ros_message)
{
  // check that the passed message is of the expected Python class
  {
    char full_classname_dest[59];
    {
      char * class_name = NULL;
      char * module_name = NULL;
      {
        PyObject * class_attr = PyObject_GetAttrString(_pymsg, "__class__");
        if (class_attr) {
          PyObject * name_attr = PyObject_GetAttrString(class_attr, "__name__");
          if (name_attr) {
            class_name = (char *)PyUnicode_1BYTE_DATA(name_attr);
            Py_DECREF(name_attr);
          }
          PyObject * module_attr = PyObject_GetAttrString(class_attr, "__module__");
          if (module_attr) {
            module_name = (char *)PyUnicode_1BYTE_DATA(module_attr);
            Py_DECREF(module_attr);
          }
          Py_DECREF(class_attr);
        }
      }
      if (!class_name || !module_name) {
        return false;
      }
      snprintf(full_classname_dest, sizeof(full_classname_dest), "%s.%s", module_name, class_name);
    }
    assert(strncmp("synapse_msgs.msg._server_communication.ServerCommunication", full_classname_dest, 58) == 0);
  }
  synapse_msgs__msg__ServerCommunication * ros_message = _ros_message;
  {  // src
    PyObject * field = PyObject_GetAttrString(_pymsg, "src");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->src = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // dest
    PyObject * field = PyObject_GetAttrString(_pymsg, "dest");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->dest = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // uid
    PyObject * field = PyObject_GetAttrString(_pymsg, "uid");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->uid = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // ack
    PyObject * field = PyObject_GetAttrString(_pymsg, "ack");
    if (!field) {
      return false;
    }
    assert(PyLong_Check(field));
    ros_message->ack = (uint8_t)PyLong_AsUnsignedLong(field);
    Py_DECREF(field);
  }
  {  // msg
    PyObject * field = PyObject_GetAttrString(_pymsg, "msg");
    if (!field) {
      return false;
    }
    assert(PyUnicode_Check(field));
    PyObject * encoded_field = PyUnicode_AsUTF8String(field);
    if (!encoded_field) {
      Py_DECREF(field);
      return false;
    }
    rosidl_runtime_c__String__assign(&ros_message->msg, PyBytes_AS_STRING(encoded_field));
    Py_DECREF(encoded_field);
    Py_DECREF(field);
  }

  return true;
}

ROSIDL_GENERATOR_C_EXPORT
PyObject * synapse_msgs__msg__server_communication__convert_to_py(void * raw_ros_message)
{
  /* NOTE(esteve): Call constructor of ServerCommunication */
  PyObject * _pymessage = NULL;
  {
    PyObject * pymessage_module = PyImport_ImportModule("synapse_msgs.msg._server_communication");
    assert(pymessage_module);
    PyObject * pymessage_class = PyObject_GetAttrString(pymessage_module, "ServerCommunication");
    assert(pymessage_class);
    Py_DECREF(pymessage_module);
    _pymessage = PyObject_CallObject(pymessage_class, NULL);
    Py_DECREF(pymessage_class);
    if (!_pymessage) {
      return NULL;
    }
  }
  synapse_msgs__msg__ServerCommunication * ros_message = (synapse_msgs__msg__ServerCommunication *)raw_ros_message;
  {  // src
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->src);
    {
      int rc = PyObject_SetAttrString(_pymessage, "src", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // dest
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->dest);
    {
      int rc = PyObject_SetAttrString(_pymessage, "dest", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // uid
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->uid);
    {
      int rc = PyObject_SetAttrString(_pymessage, "uid", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // ack
    PyObject * field = NULL;
    field = PyLong_FromUnsignedLong(ros_message->ack);
    {
      int rc = PyObject_SetAttrString(_pymessage, "ack", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }
  {  // msg
    PyObject * field = NULL;
    field = PyUnicode_DecodeUTF8(
      ros_message->msg.data,
      strlen(ros_message->msg.data),
      "replace");
    if (!field) {
      return NULL;
    }
    {
      int rc = PyObject_SetAttrString(_pymessage, "msg", field);
      Py_DECREF(field);
      if (rc) {
        return NULL;
      }
    }
  }

  // ownership of _pymessage is transferred to the caller
  return _pymessage;
}
