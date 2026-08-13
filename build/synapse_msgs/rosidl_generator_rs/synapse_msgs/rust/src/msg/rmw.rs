#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};


#[link(name = "synapse_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__BezierCurve() -> *const std::ffi::c_void;
}

#[link(name = "synapse_msgs__rosidl_generator_c")]
extern "C" {
    fn synapse_msgs__msg__BezierCurve__init(msg: *mut BezierCurve) -> bool;
    fn synapse_msgs__msg__BezierCurve__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<BezierCurve>, size: usize) -> bool;
    fn synapse_msgs__msg__BezierCurve__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<BezierCurve>);
    fn synapse_msgs__msg__BezierCurve__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<BezierCurve>, out_seq: *mut rosidl_runtime_rs::Sequence<BezierCurve>) -> bool;
}

// Corresponds to synapse_msgs__msg__BezierCurve
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BezierCurve {

    // This member is not documented.
    #[allow(missing_docs)]
    pub time_stop: u64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub x: rosidl_runtime_rs::Sequence<f64>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: rosidl_runtime_rs::Sequence<f64>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub z: rosidl_runtime_rs::Sequence<f64>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub yaw: rosidl_runtime_rs::Sequence<f64>,

}



impl Default for BezierCurve {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !synapse_msgs__msg__BezierCurve__init(&mut msg as *mut _) {
        panic!("Call to synapse_msgs__msg__BezierCurve__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for BezierCurve {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__BezierCurve__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__BezierCurve__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__BezierCurve__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for BezierCurve {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for BezierCurve where Self: Sized {
  const TYPE_NAME: &'static str = "synapse_msgs/msg/BezierCurve";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__BezierCurve() }
  }
}


#[link(name = "synapse_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__BezierTrajectory() -> *const std::ffi::c_void;
}

#[link(name = "synapse_msgs__rosidl_generator_c")]
extern "C" {
    fn synapse_msgs__msg__BezierTrajectory__init(msg: *mut BezierTrajectory) -> bool;
    fn synapse_msgs__msg__BezierTrajectory__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<BezierTrajectory>, size: usize) -> bool;
    fn synapse_msgs__msg__BezierTrajectory__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<BezierTrajectory>);
    fn synapse_msgs__msg__BezierTrajectory__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<BezierTrajectory>, out_seq: *mut rosidl_runtime_rs::Sequence<BezierTrajectory>) -> bool;
}

// Corresponds to synapse_msgs__msg__BezierTrajectory
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BezierTrajectory {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub time_start: u64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub curves: rosidl_runtime_rs::Sequence<super::super::msg::rmw::BezierCurve>,

}



impl Default for BezierTrajectory {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !synapse_msgs__msg__BezierTrajectory__init(&mut msg as *mut _) {
        panic!("Call to synapse_msgs__msg__BezierTrajectory__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for BezierTrajectory {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__BezierTrajectory__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__BezierTrajectory__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__BezierTrajectory__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for BezierTrajectory {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for BezierTrajectory where Self: Sized {
  const TYPE_NAME: &'static str = "synapse_msgs/msg/BezierTrajectory";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__BezierTrajectory() }
  }
}


#[link(name = "synapse_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__Status() -> *const std::ffi::c_void;
}

#[link(name = "synapse_msgs__rosidl_generator_c")]
extern "C" {
    fn synapse_msgs__msg__Status__init(msg: *mut Status) -> bool;
    fn synapse_msgs__msg__Status__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<Status>, size: usize) -> bool;
    fn synapse_msgs__msg__Status__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<Status>);
    fn synapse_msgs__msg__Status__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<Status>, out_seq: *mut rosidl_runtime_rs::Sequence<Status>) -> bool;
}

// Corresponds to synapse_msgs__msg__Status
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Status {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::rmw::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub arming: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub joy: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fuel: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub mode: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub safety: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub synapse: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub status_message: rosidl_runtime_rs::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub fuel_percentage: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub power: f32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub request_seq: u32,


    // This member is not documented.
    #[allow(missing_docs)]
    pub request_rejected: bool,

}

impl Status {

    // This constant is not documented.
    #[allow(missing_docs)]
    pub const ARMING_UNKNOWN: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const ARMING_DISARMED: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const ARMING_ARMED: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const FUEL_UNKNOWN: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const FUEL_CRITICAL: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const FUEL_LOW: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const FUEL_NOMINAL: u8 = 3;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const FUEL_OVER_CAPACITY: u8 = 4;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const JOY_UNKNOWN: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const JOY_DISABLED: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const JOY_LOSS: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const JOY_NOMINAL: u8 = 3;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const MODE_UNKNOWN: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const MODE_MANUAL: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const MODE_AUTO: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const MODE_CMD_VEL: u8 = 3;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const MODE_CALIBRATION: u8 = 4;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SAFETY_UNKNOWN: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SAFETY_SAFE: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SAFETY_UNSAFE: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SYNAPSE_UNKNOWN: u8 = 0;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SYNAPSE_DISABLED: u8 = 1;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SYNAPSE_LOSS: u8 = 2;


    // This constant is not documented.
    #[allow(missing_docs)]
    pub const SYNAPSE_NOMINAL: u8 = 3;

}


impl Default for Status {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !synapse_msgs__msg__Status__init(&mut msg as *mut _) {
        panic!("Call to synapse_msgs__msg__Status__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for Status {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__Status__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__Status__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__Status__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for Status {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for Status where Self: Sized {
  const TYPE_NAME: &'static str = "synapse_msgs/msg/Status";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__Status() }
  }
}


#[link(name = "synapse_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__EdgeVectors() -> *const std::ffi::c_void;
}

#[link(name = "synapse_msgs__rosidl_generator_c")]
extern "C" {
    fn synapse_msgs__msg__EdgeVectors__init(msg: *mut EdgeVectors) -> bool;
    fn synapse_msgs__msg__EdgeVectors__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<EdgeVectors>, size: usize) -> bool;
    fn synapse_msgs__msg__EdgeVectors__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<EdgeVectors>);
    fn synapse_msgs__msg__EdgeVectors__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<EdgeVectors>, out_seq: *mut rosidl_runtime_rs::Sequence<EdgeVectors>) -> bool;
}

// Corresponds to synapse_msgs__msg__EdgeVectors
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct EdgeVectors {

    // This member is not documented.
    #[allow(missing_docs)]
    pub vector_1: [geometry_msgs::msg::rmw::Point; 2],


    // This member is not documented.
    #[allow(missing_docs)]
    pub vector_2: [geometry_msgs::msg::rmw::Point; 2],


    // This member is not documented.
    #[allow(missing_docs)]
    pub vector_count: u8,


    // This member is not documented.
    #[allow(missing_docs)]
    pub image_height: u16,


    // This member is not documented.
    #[allow(missing_docs)]
    pub image_width: u16,

}



impl Default for EdgeVectors {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !synapse_msgs__msg__EdgeVectors__init(&mut msg as *mut _) {
        panic!("Call to synapse_msgs__msg__EdgeVectors__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for EdgeVectors {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__EdgeVectors__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__EdgeVectors__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__EdgeVectors__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for EdgeVectors {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for EdgeVectors where Self: Sized {
  const TYPE_NAME: &'static str = "synapse_msgs/msg/EdgeVectors";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__EdgeVectors() }
  }
}


#[link(name = "synapse_msgs__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__ServerCommunication() -> *const std::ffi::c_void;
}

#[link(name = "synapse_msgs__rosidl_generator_c")]
extern "C" {
    fn synapse_msgs__msg__ServerCommunication__init(msg: *mut ServerCommunication) -> bool;
    fn synapse_msgs__msg__ServerCommunication__Sequence__init(seq: *mut rosidl_runtime_rs::Sequence<ServerCommunication>, size: usize) -> bool;
    fn synapse_msgs__msg__ServerCommunication__Sequence__fini(seq: *mut rosidl_runtime_rs::Sequence<ServerCommunication>);
    fn synapse_msgs__msg__ServerCommunication__Sequence__copy(in_seq: &rosidl_runtime_rs::Sequence<ServerCommunication>, out_seq: *mut rosidl_runtime_rs::Sequence<ServerCommunication>) -> bool;
}

// Corresponds to synapse_msgs__msg__ServerCommunication
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]


// This struct is not documented.
#[allow(missing_docs)]

#[repr(C)]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct ServerCommunication {
    /// ID for the source component (Buggy-1, Server-2)
    pub src: u8,

    /// ID for the destination component (Buggy-1, Server-2)
    pub dest: u8,

    /// Message ID / Unique identifier counter (Different Base counter for Buggy and Server)
    pub uid: u8,

    /// Status field (0 for Blank, 1 for Ack)
    pub ack: u8,

    /// Variable-length byte array for the payload string
    pub msg: rosidl_runtime_rs::String,

}



impl Default for ServerCommunication {
  fn default() -> Self {
    unsafe {
      let mut msg = std::mem::zeroed();
      if !synapse_msgs__msg__ServerCommunication__init(&mut msg as *mut _) {
        panic!("Call to synapse_msgs__msg__ServerCommunication__init() failed");
      }
      msg
    }
  }
}

impl rosidl_runtime_rs::SequenceAlloc for ServerCommunication {
  fn sequence_init(seq: &mut rosidl_runtime_rs::Sequence<Self>, size: usize) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__ServerCommunication__Sequence__init(seq as *mut _, size) }
  }
  fn sequence_fini(seq: &mut rosidl_runtime_rs::Sequence<Self>) {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__ServerCommunication__Sequence__fini(seq as *mut _) }
  }
  fn sequence_copy(in_seq: &rosidl_runtime_rs::Sequence<Self>, out_seq: &mut rosidl_runtime_rs::Sequence<Self>) -> bool {
    // SAFETY: This is safe since the pointer is guaranteed to be valid/initialized.
    unsafe { synapse_msgs__msg__ServerCommunication__Sequence__copy(in_seq, out_seq as *mut _) }
  }
}

impl rosidl_runtime_rs::Message for ServerCommunication {
  type RmwMsg = Self;
  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> { msg_cow }
  fn from_rmw_message(msg: Self::RmwMsg) -> Self { msg }
}

impl rosidl_runtime_rs::RmwMessage for ServerCommunication where Self: Sized {
  const TYPE_NAME: &'static str = "synapse_msgs/msg/ServerCommunication";
  fn get_type_support() -> *const std::ffi::c_void {
    // SAFETY: No preconditions for this function.
    unsafe { rosidl_typesupport_c__get_message_type_support_handle__synapse_msgs__msg__ServerCommunication() }
  }
}


