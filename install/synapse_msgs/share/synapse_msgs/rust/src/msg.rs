#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to synapse_msgs__msg__BezierCurve

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BezierCurve {

    // This member is not documented.
    #[allow(missing_docs)]
    pub time_stop: u64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub x: Vec<f64>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: Vec<f64>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub z: Vec<f64>,


    // This member is not documented.
    #[allow(missing_docs)]
    pub yaw: Vec<f64>,

}



impl Default for BezierCurve {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::BezierCurve::default())
  }
}

impl rosidl_runtime_rs::Message for BezierCurve {
  type RmwMsg = super::msg::rmw::BezierCurve;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        time_stop: msg.time_stop,
        x: msg.x.into(),
        y: msg.y.into(),
        z: msg.z.into(),
        yaw: msg.yaw.into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      time_stop: msg.time_stop,
        x: msg.x.as_slice().into(),
        y: msg.y.as_slice().into(),
        z: msg.z.as_slice().into(),
        yaw: msg.yaw.as_slice().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      time_stop: msg.time_stop,
      x: msg.x
          .into_iter()
          .collect(),
      y: msg.y
          .into_iter()
          .collect(),
      z: msg.z
          .into_iter()
          .collect(),
      yaw: msg.yaw
          .into_iter()
          .collect(),
    }
  }
}


// Corresponds to synapse_msgs__msg__BezierTrajectory

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct BezierTrajectory {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


    // This member is not documented.
    #[allow(missing_docs)]
    pub time_start: u64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub curves: Vec<super::msg::BezierCurve>,

}



impl Default for BezierTrajectory {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::BezierTrajectory::default())
  }
}

impl rosidl_runtime_rs::Message for BezierTrajectory {
  type RmwMsg = super::msg::rmw::BezierTrajectory;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        time_start: msg.time_start,
        curves: msg.curves
          .into_iter()
          .map(|elem| super::msg::BezierCurve::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      time_start: msg.time_start,
        curves: msg.curves
          .iter()
          .map(|elem| super::msg::BezierCurve::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      time_start: msg.time_start,
      curves: msg.curves
          .into_iter()
          .map(super::msg::BezierCurve::from_rmw_message)
          .collect(),
    }
  }
}


// Corresponds to synapse_msgs__msg__Status

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Status {

    // This member is not documented.
    #[allow(missing_docs)]
    pub header: std_msgs::msg::Header,


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
    pub status_message: std::string::String,


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Status::default())
  }
}

impl rosidl_runtime_rs::Message for Status {
  type RmwMsg = super::msg::rmw::Status;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Owned(msg.header)).into_owned(),
        arming: msg.arming,
        joy: msg.joy,
        fuel: msg.fuel,
        mode: msg.mode,
        safety: msg.safety,
        synapse: msg.synapse,
        status_message: msg.status_message.as_str().into(),
        fuel_percentage: msg.fuel_percentage,
        power: msg.power,
        request_seq: msg.request_seq,
        request_rejected: msg.request_rejected,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        header: std_msgs::msg::Header::into_rmw_message(std::borrow::Cow::Borrowed(&msg.header)).into_owned(),
      arming: msg.arming,
      joy: msg.joy,
      fuel: msg.fuel,
      mode: msg.mode,
      safety: msg.safety,
      synapse: msg.synapse,
        status_message: msg.status_message.as_str().into(),
      fuel_percentage: msg.fuel_percentage,
      power: msg.power,
      request_seq: msg.request_seq,
      request_rejected: msg.request_rejected,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      header: std_msgs::msg::Header::from_rmw_message(msg.header),
      arming: msg.arming,
      joy: msg.joy,
      fuel: msg.fuel,
      mode: msg.mode,
      safety: msg.safety,
      synapse: msg.synapse,
      status_message: msg.status_message.to_string(),
      fuel_percentage: msg.fuel_percentage,
      power: msg.power,
      request_seq: msg.request_seq,
      request_rejected: msg.request_rejected,
    }
  }
}


// Corresponds to synapse_msgs__msg__EdgeVectors

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct EdgeVectors {

    // This member is not documented.
    #[allow(missing_docs)]
    pub vector_1: [geometry_msgs::msg::Point; 2],


    // This member is not documented.
    #[allow(missing_docs)]
    pub vector_2: [geometry_msgs::msg::Point; 2],


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
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::EdgeVectors::default())
  }
}

impl rosidl_runtime_rs::Message for EdgeVectors {
  type RmwMsg = super::msg::rmw::EdgeVectors;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        vector_1: msg.vector_1
          .map(|elem| geometry_msgs::msg::Point::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned()),
        vector_2: msg.vector_2
          .map(|elem| geometry_msgs::msg::Point::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned()),
        vector_count: msg.vector_count,
        image_height: msg.image_height,
        image_width: msg.image_width,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        vector_1: msg.vector_1
          .iter()
          .map(|elem| geometry_msgs::msg::Point::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect::<Vec<_>>()
          .try_into()
          .unwrap(),
        vector_2: msg.vector_2
          .iter()
          .map(|elem| geometry_msgs::msg::Point::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect::<Vec<_>>()
          .try_into()
          .unwrap(),
      vector_count: msg.vector_count,
      image_height: msg.image_height,
      image_width: msg.image_width,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      vector_1: msg.vector_1
        .map(geometry_msgs::msg::Point::from_rmw_message),
      vector_2: msg.vector_2
        .map(geometry_msgs::msg::Point::from_rmw_message),
      vector_count: msg.vector_count,
      image_height: msg.image_height,
      image_width: msg.image_width,
    }
  }
}


// Corresponds to synapse_msgs__msg__ServerCommunication

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
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
    pub msg: std::string::String,

}



impl Default for ServerCommunication {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::ServerCommunication::default())
  }
}

impl rosidl_runtime_rs::Message for ServerCommunication {
  type RmwMsg = super::msg::rmw::ServerCommunication;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        src: msg.src,
        dest: msg.dest,
        uid: msg.uid,
        ack: msg.ack,
        msg: msg.msg.as_str().into(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      src: msg.src,
      dest: msg.dest,
      uid: msg.uid,
      ack: msg.ack,
        msg: msg.msg.as_str().into(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      src: msg.src,
      dest: msg.dest,
      uid: msg.uid,
      ack: msg.ack,
      msg: msg.msg.to_string(),
    }
  }
}


