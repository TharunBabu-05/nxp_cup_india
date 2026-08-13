# ROS2 Integration Guide — NXP Cup India 2026
## Integrating YOLOv8 Object Detection into `b3rb_ros_object_recog.py`

---

## Overview

This guide covers integrating the trained `best.pt` model into the BeagleBoard B3RB ROS2 autonomy stack for sign board detection.

**Target file**: `b3rb_ros_object_recog.py`  
**Model**: `models/best.pt` (YOLOv8n)  
**Classes**: A, B, C, Left, Right, Straight, X, Y, Z  
**Input**: Compressed camera image (ROS2 topic)  
**Output**: Detection array message

---

## 1. Prerequisites

```bash
# Install Ultralytics in your ROS2 Python environment
pip install ultralytics opencv-python

# Verify
python3 -c "from ultralytics import YOLO; print('OK')"
```

---

## 2. Required ROS2 Topics

| Direction | Topic | Type | Description |
|-----------|-------|------|-------------|
| Input | `/camera/image_raw` | `sensor_msgs/Image` | Raw camera frame |
| Input | `/camera/image_compressed` | `sensor_msgs/CompressedImage` | Compressed frame (preferred) |
| Output | `/object_detections` | `vision_msgs/Detection2DArray` | Detection results |
| Output | `/sign_class` | `std_msgs/String` | Most confident sign class name |
| Output | `/detection_image` | `sensor_msgs/Image` | Annotated frame (debug) |

---

## 3. ROS2 Node Implementation

```python
#!/usr/bin/env python3
"""
b3rb_ros_object_recog.py — NXP Cup India 2026
Sign Board Detection Node using YOLOv8

Drop-in integration for BeagleBoard B3RB autonomy stack.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CompressedImage
from std_msgs.msg import String
from cv_bridge import CvBridge

import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

# ── Class configuration ───────────────────────────────────────────────────────
CLASS_NAMES = ["A", "B", "C", "Left", "Right", "Straight", "X", "Y", "Z"]
MODEL_PATH  = "/path/to/NXPCUP_2026.v2-v1_a.yolov8/models/best.pt"
CONF_THRESH = 0.35   # optimal threshold from confidence_sweep.png
IOU_THRESH  = 0.60
IMGSZ       = 512


class SignDetectorNode(Node):

    def __init__(self):
        super().__init__("sign_detector")

        # ── Parameters ───────────────────────────────────────────────────────
        self.declare_parameter("model_path",  MODEL_PATH)
        self.declare_parameter("conf_thresh", CONF_THRESH)
        self.declare_parameter("iou_thresh",  IOU_THRESH)
        self.declare_parameter("device",      "0")

        model_path  = self.get_parameter("model_path").value
        conf_thresh = self.get_parameter("conf_thresh").value
        device      = self.get_parameter("device").value

        # ── Model ─────────────────────────────────────────────────────────────
        self.get_logger().info(f"Loading model: {model_path}")
        self.model = YOLO(model_path)
        self.conf  = float(conf_thresh)
        self.iou   = float(iou_thresh)
        self.bridge = CvBridge()

        # ── Subscribers ───────────────────────────────────────────────────────
        self.create_subscription(
            CompressedImage, "/camera/image_compressed",
            self.image_callback, 10
        )

        # ── Publishers ────────────────────────────────────────────────────────
        self.pub_sign  = self.create_publisher(String, "/sign_class", 10)
        self.pub_debug = self.create_publisher(Image, "/detection_image", 10)

        self.get_logger().info("SignDetectorNode ready.")

    def image_callback(self, msg: CompressedImage) -> None:
        # Decode compressed image
        np_arr = np.frombuffer(msg.data, np.uint8)
        frame  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return

        # Run inference
        results = self.model.predict(
            source  = frame,
            conf    = self.conf,
            iou     = self.iou,
            imgsz   = IMGSZ,
            verbose = False,
            device  = "0",
        )

        detections = results[0].boxes
        top_sign   = self._get_top_class(detections)

        # Publish sign class
        if top_sign:
            msg_str = String()
            msg_str.data = top_sign
            self.pub_sign.publish(msg_str)

        # Publish annotated debug frame
        annotated = results[0].plot()
        debug_msg = self.bridge.cv2_to_imgmsg(annotated, encoding="bgr8")
        debug_msg.header = msg.header
        self.pub_debug.publish(debug_msg)

    def _get_top_class(self, boxes) -> str | None:
        """Return the highest-confidence detection class name."""
        if boxes is None or len(boxes) == 0:
            return None
        best_conf = 0.0
        best_cls  = None
        for box in boxes:
            conf = float(box.conf[0])
            cls  = int(box.cls[0])
            if conf > best_conf:
                best_conf = conf
                best_cls  = CLASS_NAMES[cls] if cls < len(CLASS_NAMES) else str(cls)
        return best_cls


def main(args=None):
    rclpy.init(args=args)
    node = SignDetectorNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
```

---

## 4. Launch Configuration

Create `launch/sign_detector.launch.py`:

```python
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package    = "your_package",
            executable = "b3rb_ros_object_recog",
            name       = "sign_detector",
            parameters = [{
                "model_path" : "/path/to/models/best.pt",
                "conf_thresh": 0.35,
                "iou_thresh" : 0.60,
                "device"     : "0",
            }],
            remappings = [
                ("/camera/image_compressed", "/b3rb/camera/compressed"),
            ],
        )
    ])
```

---

## 5. Dependencies for `package.xml`

```xml
<depend>rclpy</depend>
<depend>sensor_msgs</depend>
<depend>std_msgs</depend>
<depend>cv_bridge</depend>
<depend>vision_msgs</depend>
```

For `setup.py`:

```python
install_requires=[
    "ultralytics",
    "opencv-python",
    "numpy",
],
```

---

## 6. Model Path Resolution

Update `MODEL_PATH` in the node, or set via ROS2 parameter:

```bash
ros2 run your_package b3rb_ros_object_recog \
  --ros-args \
  -p model_path:=/absolute/path/to/models/best.pt \
  -p conf_thresh:=0.35
```

---

## 7. Performance Notes

| Mode | Latency | Notes |
|------|---------|-------|
| YOLOv8n GPU (FP32) | ~5–15 ms | Recommended |
| YOLOv8n GPU (FP16) | ~3–8 ms  | Use `best.engine` (TensorRT) |
| YOLOv8n CPU | ~80–200 ms | Fallback only |

For Jetson Nano / embedded deployment, use the TensorRT export:
```python
model = YOLO("exports/best.engine")  # TensorRT FP16
```

---

## 8. Output Signal Mapping

```
Detected class → Robot behavior:

"Left"     → Turn Left
"Right"    → Turn Right
"Straight" → Go Straight
"A"–"C"   → Zone marker (log + continue)
"X","Y","Z"→ Checkpoint marker
```

---

## 9. Verification Checklist

- [ ] `best.pt` loads without error
- [ ] Camera topic is publishing
- [ ] `/sign_class` topic shows correct class
- [ ] `/detection_image` shows bounding boxes
- [ ] Inference latency < 50 ms per frame
- [ ] No memory leaks after 10-minute run

---

*Generated by NXP Cup India 2026 pipeline — docs/ros2_integration.md*
