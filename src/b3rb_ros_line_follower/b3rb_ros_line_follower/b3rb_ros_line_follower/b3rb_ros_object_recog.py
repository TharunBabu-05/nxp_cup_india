# Copyright 2024-2026 NXP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
import cv2
import numpy as np
import os
import time

# ── YOLOv8 (ultralytics) via torch ───────────────────────────────
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# ── Tuning ────────────────────────────────────────────────────────
CONF_THRESHOLD      = 0.55   # minimum detection confidence
SIGN_CONFIRM_COUNT  = 3      # consecutive frames before publishing
PUBLISH_COOLDOWN_S  = 1.0    # seconds between publishing the same sign

# YOLOv8 classes (must match data.yaml order):
# ['A', 'B', 'C', 'Left', 'Right', 'Straight', 'X', 'Y', 'Z']
CLASS_NAMES = ['A', 'B', 'C', 'Left', 'Right', 'Straight', 'X', 'Y', 'Z']

# Mapping to canonical topic strings
DESTINATION_MAP = {
    'A': 'PATIENT_1',
    'B': 'PATIENT_2',
    'C': 'PATIENT_3',
    'X': 'HOSPITAL_1',
    'Y': 'HOSPITAL_2',
    'Z': 'HOSPITAL_3',
}
DIRECTION_MAP = {
    'Left':     'LEFT',
    'Right':    'RIGHT',
    'Straight': 'STRAIGHT',
}


class ObjectRecognizer(Node):
    """
    ROS 2 Node that classifies traffic sign boards using the supplied YOLOv8 model.
    Falls back to a Keras/OpenCV placeholder if the model is absent.

    Published topic: /sign_board_detection
    Message format:  "<DESTINATION>:<DIRECTION>"
    Example:         "HOSPITAL_2:LEFT"
    """

    def __init__(self):
        super().__init__('object_recognizer')

        self.subscription_camera = self.create_subscription(
            CompressedImage,
            '/camera/image_raw/compressed',
            self.camera_image_callback,
            10)

        self.publisher_sign = self.create_publisher(String, '/sign_board_detection', 10)

        self.model = None
        self._load_model()

        self._last_dest = None
        self._last_dest_time = 0.0
        self._last_dir = None
        self._last_dir_time = 0.0

        # Debounce state
        self._candidate: str = ''
        self._candidate_count: int = 0
        self._last_published: str = ''
        self._last_publish_time: float = 0.0

        self.get_logger().info('[DETECT] Object Recognizer ready.')

    # ── model loading ─────────────────────────────────────────────
    def _load_model(self):
        """Try to load the YOLOv8 best.pt from the created_model directory."""
        if not YOLO_AVAILABLE:
            self.get_logger().warn('[DETECT] ultralytics not installed; sign detection disabled.')
            return

        # Search path: alongside this script, or in created_model directory
        candidates = [
            os.path.join(
                os.path.expanduser('~'),
                'cognipilot', 'cranium',
                'created_model_NXPCUP_2026.v2-v1_yolov8',
                'content', 'NXPCUP_2026.v2-v1_a.yolov8',
                'models', 'best.pt'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'best.pt'),
        ]

        for path in candidates:
            if os.path.exists(path):
                try:
                    self.model = YOLO(path)
                    self.get_logger().info(f'[DETECT] Loaded YOLOv8 model from {path}')
                    return
                except Exception as e:
                    self.get_logger().error(f'[DETECT] Failed to load model: {e}')

        self.get_logger().warn('[DETECT] YOLOv8 model not found. Sign detection disabled.')

    # ── camera callback ───────────────────────────────────────────
    def camera_image_callback(self, message):
        np_arr = np.frombuffer(message.data, np.uint8)
        image   = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            return

        result = self.classify_sign(image)
        if result is None:
            self._candidate_count = 0
            return

        now = time.time()

        # Consecutive-frame confirmation
        if result == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate       = result
            self._candidate_count = 1

        if self._candidate_count < SIGN_CONFIRM_COUNT:
            return

        # Same-result cooldown
        if result == self._last_published:
            if now - self._last_publish_time < PUBLISH_COOLDOWN_S:
                return

        self._last_published    = result
        self._last_publish_time = now

        msg = String()
        msg.data = result
        self.publisher_sign.publish(msg)
        self.get_logger().info(f'[DETECT] Sign published: {result}')

    # ── classification ────────────────────────────────────────────
    def classify_sign(self, image):
        """
        Run YOLOv8 inference.
        Returns a string like "HOSPITAL_2:LEFT" or None.
        """
        if self.model is None:
            return None

        try:
            results = self.model(image, verbose=False, conf=CONF_THRESHOLD)
            if not results or len(results) == 0:
                pass
            else:
                boxes = results[0].boxes
                if boxes is not None and len(boxes) > 0:
                    # Collect destination and direction detections separately
                    destination_hits = []  # (conf, label_str)
                    direction_hits   = []  # (conf, label_str)

                    for box in boxes:
                        cls_id = int(box.cls[0].item())
                        conf   = float(box.conf[0].item())
                        if cls_id >= len(CLASS_NAMES):
                            continue
                        label = CLASS_NAMES[cls_id]

                        if label in DESTINATION_MAP:
                            destination_hits.append((conf, DESTINATION_MAP[label]))
                        elif label in DIRECTION_MAP:
                            direction_hits.append((conf, DIRECTION_MAP[label]))

                    if destination_hits:
                        best_dest = max(destination_hits, key=lambda x: x[0])[1]
                        self._last_dest = best_dest
                        self._last_dest_time = time.time()
                        
                    if direction_hits:
                        best_dir = max(direction_hits, key=lambda x: x[0])[1]
                        self._last_dir = best_dir
                        self._last_dir_time = time.time()
            
            now = time.time()
            dest = self._last_dest if (now - self._last_dest_time < 2.5) else None
            dir_ = self._last_dir if (now - self._last_dir_time < 2.5) else None
            
            if dest and dir_:
                return f'{dest}:{dir_}'
            elif dest:
                return f'{dest}:STRAIGHT'
            elif dir_:
                return f'UNKNOWN:{dir_}'

        except Exception as e:
            self.get_logger().debug(f'[DETECT] Inference error: {e}')

        return None


def main(args=None):
    rclpy.init(args=args)
    node = ObjectRecognizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
