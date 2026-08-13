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
    It matches multiple destinations and directions per frame using X-coordinate proximity
    (since arrows are directly underneath letters on the sign board).
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

        # Track consecutive detections for each unique sign string independently
        self._candidates = {}  # dict[sign_str, count]

        # Locked signs (we can lock multiple simultaneously if they are all on the board)
        self._locked_signs = {} # dict[sign_str, (lock_start_time, last_publish_time)]

        self.get_logger().info('[DETECT] Object Recognizer ready (Multi-sign spatial pairing).')

    def _load_model(self):
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

    def camera_image_callback(self, message):
        np_arr = np.frombuffer(message.data, np.uint8)
        image  = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            return

        now = time.time()

        # ── Handle Locked Signs ──
        active_locks = []
        for sign, (start_t, last_pub_t) in list(self._locked_signs.items()):
            if now - start_t < LOCK_RELEASE_S:
                if now - last_pub_t >= (1.0 / LOCK_PUBLISH_HZ):
                    self._publish(sign)
                    self._locked_signs[sign] = (start_t, now)
                active_locks.append(sign)
            else:
                self.get_logger().info(f'[DETECT] Lock released: {sign}')
                del self._locked_signs[sign]
                if sign in self._candidates:
                    del self._candidates[sign]

        # ── Fresh inference ──
        detected_signs = self._classify(image)
        
        # Update candidate counts
        new_candidates = {}
        for sign in detected_signs:
            # Skip if already locked
            if sign in self._locked_signs:
                continue
                
            cnt = self._candidates.get(sign, 0) + 1
            new_candidates[sign] = cnt
            
            if cnt >= SIGN_CONFIRM_COUNT:
                # LOCK this sign
                self._locked_signs[sign] = (now, 0.0) # 0.0 forces immediate publish next tick
                self.get_logger().info(f'[DETECT] LOCKED sign: {sign}')
                new_candidates[sign] = 0 # reset
                
        self._candidates = new_candidates

    def _publish(self, sign: str):
        msg = String()
        msg.data = sign
        self.publisher_sign.publish(msg)
        self.get_logger().info(f'[DETECT] Sign published: {sign}')

    def _classify(self, image):
        """
        Returns a list of sign strings found in this frame.
        Pairs each destination with the direction directly below it (closest X).
        """
        if self.model is None:
            return []

        try:
            results = self.model(image, verbose=False, conf=CONF_THRESHOLD)
            if not results or len(results) == 0:
                return []

            boxes = results[0].boxes
            if boxes is None or len(boxes) == 0:
                return []

            destination_hits = []  # (conf, label_str, cx, cy)
            direction_hits   = []  # (conf, label_str, cx, cy)

            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf   = float(box.conf[0].item())
                if cls_id >= len(CLASS_NAMES):
                    continue
                label = CLASS_NAMES[cls_id]
                
                coords = box.xyxy[0].tolist()
                cx = (coords[0] + coords[2]) / 2.0
                cy = (coords[1] + coords[3]) / 2.0

                if label in DESTINATION_MAP:
                    destination_hits.append((conf, DESTINATION_MAP[label], cx, cy))
                elif label in DIRECTION_MAP:
                    direction_hits.append((conf, DIRECTION_MAP[label], cx, cy))

            found_signs = []
            
            # For each destination, find the horizontally closest direction arrow
            for dest_conf, dest_label, dest_cx, dest_cy in destination_hits:
                if direction_hits:
                    # Find arrow with minimum X-axis distance to the letter
                    best_dir = min(direction_hits, key=lambda d: abs(d[2] - dest_cx))
                    
                    # Optional: We could check if it's within a reasonable threshold, 
                    # but since they are on the same board, min X distance is robust.
                    dir_label = best_dir[1]
                    found_signs.append(f'{dest_label}:{dir_label}')
                else:
                    # If absolutely no arrows detected, fallback to straight
                    found_signs.append(f'{dest_label}:STRAIGHT')

            return found_signs

        except Exception as e:
            self.get_logger().debug(f'[DETECT] Inference error: {e}')

        return []


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
