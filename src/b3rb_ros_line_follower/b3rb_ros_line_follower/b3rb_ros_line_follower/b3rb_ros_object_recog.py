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

# ── YOLOv8 (ultralytics) via torch / ONNX ────────────────────────
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# ── Tuning ────────────────────────────────────────────────────────
CONF_THRESHOLD      = 0.50   # minimum detection confidence
SIGN_CONFIRM_COUNT  = 3      # consecutive frames before locking a sign
LOCK_PUBLISH_HZ     = 2.0    # while locked, re-publish at this rate (seconds)
LOCK_RELEASE_S      = 6.0    # release the lock after this many seconds (safety)

# YOLOv8 classes  (MUST match data.yaml order in the new model):
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

# ── New model path ────────────────────────────────────────────────
NEW_MODEL_PATH = os.path.join(
    os.path.expanduser('~'),
    'cognipilot', 'cranium',
    'created_model_NXPCUP_2026.v2-v1_yolov8',
    'content', 'NXPCUP_2026.v2-v1_a.yolov8',
    'new', 'best.onnx')

FALLBACK_MODEL_PATH = os.path.join(
    os.path.expanduser('~'),
    'cognipilot', 'cranium',
    'created_model_NXPCUP_2026.v2-v1_yolov8',
    'content', 'NXPCUP_2026.v2-v1_a.yolov8',
    'models', 'best.pt')


class ObjectRecognizer(Node):
    """
    ROS 2 Node that classifies traffic sign boards using the new ONNX YOLOv8 model.

    Sign-lock behaviour
    ───────────────────
    Once SIGN_CONFIRM_COUNT consecutive frames agree on a (destination, direction)
    pair, the node LOCKS onto that reading and re-publishes it at LOCK_PUBLISH_HZ
    until LOCK_RELEASE_S seconds have elapsed.  This prevents the buggy from
    missing the turn command because the detection blinked for only one frame.

    Published topic: /sign_board_detection
    Message format:  "<DESTINATION>:<DIRECTION>"
    Example:         "PATIENT_1:RIGHT"
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

        # Per-frame detection buffers (for this frame only, no carry-over)
        self._last_dest = None
        self._last_dest_time = 0.0
        self._last_dir = None
        self._last_dir_time = 0.0

        # Consecutive-frame confirmation window
        self._candidate: str = ''
        self._candidate_count: int = 0

        # Sign-lock state
        self._locked_sign: str = ''          # e.g. "PATIENT_1:RIGHT"
        self._lock_start_t: float = 0.0      # when the lock was acquired
        self._last_lock_publish_t: float = 0.0

        self.get_logger().info('[DETECT] Object Recognizer ready (new ONNX model, sign-lock).')

    # ── model loading ─────────────────────────────────────────────
    def _load_model(self):
        """Load the new ONNX model, fall back to old .pt if unavailable."""
        if not YOLO_AVAILABLE:
            self.get_logger().warn('[DETECT] ultralytics not installed; sign detection disabled.')
            return

        candidates = [NEW_MODEL_PATH, FALLBACK_MODEL_PATH]

        for path in candidates:
            if os.path.exists(path):
                try:
                    self.model = YOLO(path, task='detect')
                    self.get_logger().info(f'[DETECT] Loaded model from {path}')
                    return
                except Exception as e:
                    self.get_logger().error(f'[DETECT] Failed to load {path}: {e}')

        self.get_logger().warn('[DETECT] No model found. Sign detection disabled.')

    # ── camera callback ───────────────────────────────────────────
    def camera_image_callback(self, message):
        np_arr = np.frombuffer(message.data, np.uint8)
        image  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            return

        now = time.time()

        # ── If locked, keep re-publishing until the lock expires ──
        if self._locked_sign:
            if now - self._lock_start_t < LOCK_RELEASE_S:
                if now - self._last_lock_publish_t >= (1.0 / LOCK_PUBLISH_HZ):
                    self._publish(self._locked_sign)
                    self._last_lock_publish_t = now
                return   # do NOT run fresh inference while locked
            else:
                self.get_logger().info(
                    f'[DETECT] Lock released: {self._locked_sign}')
                self._locked_sign = ''
                self._candidate   = ''
                self._candidate_count = 0

        # ── Fresh inference ───────────────────────────────────────
        result = self._classify(image)

        if result is None:
            # No detection → reset confirmation window
            self._candidate_count = 0
            return

        # Accumulate consecutive confirmations
        if result == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate       = result
            self._candidate_count = 1

        if self._candidate_count >= SIGN_CONFIRM_COUNT:
            # LOCK this sign
            self._locked_sign          = result
            self._lock_start_t         = now
            self._last_lock_publish_t  = 0.0   # force immediate publish
            self._candidate_count      = 0
            self.get_logger().info(
                f'[DETECT] LOCKED sign: {result}')

    # ── publish helper ────────────────────────────────────────────
    def _publish(self, sign: str):
        msg = String()
        msg.data = sign
        self.publisher_sign.publish(msg)
        self.get_logger().info(f'[DETECT] Sign published: {sign}')

    # ── YOLOv8 inference ─────────────────────────────────────────
    def _classify(self, image):
        """
        Run YOLOv8 inference on a single frame.
        Returns a string like "HOSPITAL_2:LEFT" or None.

        This method does NOT use any time-based carry-over cache — it looks
        ONLY at what is visible right now.  Dest + Dir must both appear in
        the same frame for a result to be returned.
        """
        if self.model is None:
            return None

        try:
            results = self.model(image, verbose=False, conf=CONF_THRESHOLD)
            if not results or len(results) == 0:
                return None

            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                return None

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

            # Both destination AND direction must be detected in the same frame
            if destination_hits and direction_hits:
                best_dest = max(destination_hits, key=lambda x: x[0])[1]
                best_dir  = max(direction_hits,   key=lambda x: x[0])[1]
                return f'{best_dest}:{best_dir}'

            # Destination only → default to STRAIGHT (don't turn)
            if destination_hits:
                best_dest = max(destination_hits, key=lambda x: x[0])[1]
                return f'{best_dest}:STRAIGHT'

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
