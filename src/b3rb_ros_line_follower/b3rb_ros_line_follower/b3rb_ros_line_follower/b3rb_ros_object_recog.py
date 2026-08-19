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

"""
b3rb_ros_object_recog.py  —  Sign detection node using YOLOv8n (train-5)

Model: /home/tharun/cognipilot/cranium/train-5/weights/best.pt
Classes (18 combined destination+direction):
  A_Left, A_Right, A_Straight   →  PATIENT_1  + direction
  B_Left, B_Right, B_Straight   →  PATIENT_2  + direction
  C_Left, C_Right, C_Straight   →  PATIENT_3  + direction
  X_Left, X_Right, X_Straight   →  HOSPITAL_1 + direction
  Y_Left, Y_Right, Y_Straight   →  HOSPITAL_2 + direction
  Z_Left, Z_Right, Z_Straight   →  HOSPITAL_3 + direction

Published topic: /sign_board_detection
Message format:  "<DESTINATION>:<DIRECTION>"
Example:         "PATIENT_1:LEFT"

Sign-lock behaviour
───────────────────
Once SIGN_CONFIRM_COUNT consecutive frames agree on the same class, the node
LOCKS on that result and re-publishes it at LOCK_PUBLISH_HZ for LOCK_RELEASE_S
seconds.  This guarantees the main FSM runner always receives the command even
when the buggy has driven slightly past the sign board.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import String
import cv2
import numpy as np
import os
import time

# ── YOLOv8 (ultralytics) ─────────────────────────────────────────
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

# ── Tuning ────────────────────────────────────────────────────────
CONF_THRESHOLD     = 0.55   # minimum detection confidence
SIGN_CONFIRM_COUNT = 3      # consecutive identical frames before locking
LOCK_PUBLISH_HZ    = 2.0    # while locked: republish this many times/sec
LOCK_RELEASE_S     = 6.0    # release lock after this many seconds

# ── Model path (primary = new train-5, fallback = old model) ─────
MODEL_PATH = os.path.expanduser(
    '~/cognipilot/cranium/train-5/weights/best.pt')
FALLBACK_MODEL_PATH = os.path.expanduser(
    '~/cognipilot/cranium/created_model_NXPCUP_2026.v2-v1_yolov8'
    '/content/NXPCUP_2026.v2-v1_a.yolov8/models/best.pt')

# ── Class-name → (destination, direction) mapping ────────────────
# Each of the 18 classes encodes BOTH the destination letter and the arrow.
CLASS_MAP = {
    # Patient 1  (A)
    'A_Left':       ('PATIENT_1',  'LEFT'),
    'A_Right':      ('PATIENT_1',  'RIGHT'),
    'A_Straight':   ('PATIENT_1',  'STRAIGHT'),
    # Patient 2  (B)
    'B_Left':       ('PATIENT_2',  'LEFT'),
    'B_Right':      ('PATIENT_2',  'RIGHT'),
    'B_Straight':   ('PATIENT_2',  'STRAIGHT'),
    # Patient 3  (C)
    'C_Left':       ('PATIENT_3',  'LEFT'),
    'C_Right':      ('PATIENT_3',  'RIGHT'),
    'C_Straight':   ('PATIENT_3',  'STRAIGHT'),
    # Hospital 1 (X)
    'X_Left':       ('HOSPITAL_1', 'LEFT'),
    'X_Right':      ('HOSPITAL_1', 'RIGHT'),
    'X_Straight':   ('HOSPITAL_1', 'STRAIGHT'),
    # Hospital 2 (Y)
    'Y_Left':       ('HOSPITAL_2', 'LEFT'),
    'Y_Right':      ('HOSPITAL_2', 'RIGHT'),
    'Y_Straight':   ('HOSPITAL_2', 'STRAIGHT'),
    # Hospital 3 (Z)
    'Z_Left':       ('HOSPITAL_3', 'LEFT'),
    'Z_Right':      ('HOSPITAL_3', 'RIGHT'),
    'Z_Straight':   ('HOSPITAL_3', 'STRAIGHT'),
}


class ObjectRecognizer(Node):

    def __init__(self):
        super().__init__('object_recognizer')

        self.subscription_camera = self.create_subscription(
            CompressedImage,
            '/camera/image_raw/compressed',
            self._cb_camera,
            10)

        self.publisher_sign = self.create_publisher(String, '/sign_board_detection', 10)

        self.model = None
        self._load_model()

        # Consecutive-frame confirmation window
        self._candidate: str = ''
        self._candidate_count: int = 0

        # Sign-lock state
        self._locked_sign: str = ''
        self._lock_start_t: float = 0.0
        self._last_lock_pub_t: float = 0.0

        self.get_logger().info(
            '[DETECT] Object Recognizer ready — YOLOv8n train-5 (18 combined classes).')

    # ── model loading ─────────────────────────────────────────────
    def _load_model(self):
        if not YOLO_AVAILABLE:
            self.get_logger().warn(
                '[DETECT] ultralytics not installed; sign detection disabled.')
            return

        for path in [MODEL_PATH, FALLBACK_MODEL_PATH]:
            if os.path.exists(path):
                try:
                    self.model = YOLO(path, task='detect')
                    self.get_logger().info(f'[DETECT] Loaded model: {path}')
                    # Log class list so we can verify in terminal
                    for idx, name in self.model.names.items():
                        self.get_logger().debug(f'  class {idx}: {name}')
                    return
                except Exception as e:
                    self.get_logger().error(f'[DETECT] Failed to load {path}: {e}')

        self.get_logger().warn('[DETECT] No model found — sign detection disabled.')

    # ── camera callback ───────────────────────────────────────────
    def _cb_camera(self, message):
        np_arr = np.frombuffer(message.data, np.uint8)
        image  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            return

        now = time.time()

        # ── While locked: keep re-publishing the locked sign ─────
        if self._locked_sign:
            if now - self._lock_start_t < LOCK_RELEASE_S:
                if now - self._last_lock_pub_t >= (1.0 / LOCK_PUBLISH_HZ):
                    self._publish(self._locked_sign)
                    self._last_lock_pub_t = now
                return   # skip fresh inference while locked
            else:
                self.get_logger().info(
                    f'[DETECT] Lock released: {self._locked_sign}')
                self._locked_sign     = ''
                self._candidate       = ''
                self._candidate_count = 0

        # ── Fresh inference ───────────────────────────────────────
        result = self._infer(image)

        if result is None:
            self._candidate_count = 0
            return

        if result == self._candidate:
            self._candidate_count += 1
        else:
            self._candidate       = result
            self._candidate_count = 1

        if self._candidate_count >= SIGN_CONFIRM_COUNT:
            self._locked_sign     = result
            self._lock_start_t    = now
            self._last_lock_pub_t = 0.0  # force immediate first publish
            self._candidate_count = 0
            self.get_logger().info(f'[DETECT] LOCKED: {result}')

    # ── publish helper ────────────────────────────────────────────
    def _publish(self, sign: str):
        msg = String()
        msg.data = sign
        self.publisher_sign.publish(msg)
        self.get_logger().info(f'[DETECT] Published: {sign}')

    # ── YOLOv8 inference ─────────────────────────────────────────
    def _infer(self, image):
        """
        Run YOLO inference and return a string like 'PATIENT_1:LEFT' or None.

        Since the model was trained on combined classes (A_Left, etc.), each
        detected box already encodes BOTH destination AND direction — no spatial
        pairing or carry-over cache needed.
        """
        if self.model is None:
            return None

        try:
            results = self.model(image, verbose=False, conf=CONF_THRESHOLD)
            if not results:
                return None

            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                return None

            # Collect all valid hits, keep the highest-confidence one
            best_conf   = -1.0
            best_result = None

            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf   = float(box.conf[0].item())

                class_name = self.model.names.get(cls_id)
                if class_name is None:
                    continue

                if class_name not in CLASS_MAP:
                    self.get_logger().debug(
                        f'[DETECT] Unknown class: {class_name}')
                    continue

                dest, direction = CLASS_MAP[class_name]

                if conf > best_conf:
                    best_conf   = conf
                    best_result = f'{dest}:{direction}'

            return best_result

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
