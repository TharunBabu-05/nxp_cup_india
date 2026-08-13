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
import time
import re

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    PYZBAR_AVAILABLE = False

# ── Tuning constants ──────────────────────────────────────────────
QR_COOLDOWN_S      = 2.0   # seconds between publishing the same QR code
QR_CONFIRM_COUNT   = 2     # consecutive frames required before publishing
PUBLISH_THROTTLE_S = 0.5   # min interval between ANY publish


class QRDetector(Node):
    """
    ROS 2 Node that processes camera images to detect and decode QR codes.
    Publishes the normalised location string on /qr_detection.
    Implements debouncing, duplicate suppression and multi-variant preprocessing.
    """

    VALID_LOCATIONS = {
        'PATIENT_1', 'PATIENT_2', 'PATIENT_3',
        'HOSPITAL_1', 'HOSPITAL_2', 'HOSPITAL_3',
        'FAKE_HOSPITAL_1', 'FAKE_HOSPITAL_2',
        'PARKED',
    }

    def __init__(self):
        super().__init__('qr_detector')

        self.subscription_camera = self.create_subscription(
            CompressedImage,
            '/camera/image_raw/compressed',
            self.camera_image_callback,
            10)

        self.publisher_qr = self.create_publisher(String, '/qr_detection', 10)

        # Debounce / cooldown state
        self._last_published_code: str = ''
        self._last_publish_time: float = 0.0
        self._candidate_code: str = ''
        self._candidate_count: int = 0

        # OpenCV QR detector (kept persistent for efficiency)
        self._cv_detector = cv2.QRCodeDetector()

        avail = 'pyzbar' if PYZBAR_AVAILABLE else 'OpenCV only'
        self.get_logger().info(f'[QR] Detector ready — backend: {avail}')

    # ── public parse helper ───────────────────────────────────────
    @staticmethod
    def normalise(raw: str) -> str:
        """
        Convert any of:
          {LOC: PATIENT_1}  /  patient_1  /  PATIENT_1
        into the canonical uppercase form e.g. 'PATIENT_1'.
        Returns '' if the token is not recognised.
        """
        if not raw:
            return ''
        # strip surrounding whitespace / braces
        cleaned = raw.strip().upper()
        # try to extract token from {LOC: TOKEN} pattern
        m = re.search(r'LOC\s*:\s*(\w+)', cleaned)
        if m:
            cleaned = m.group(1)
        # remove spaces/underscores variations
        cleaned = cleaned.replace(' ', '_')
        return cleaned

    # ── camera callback ───────────────────────────────────────────
    def camera_image_callback(self, message):
        np_arr = np.frombuffer(message.data, np.uint8)
        image   = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if image is None:
            return

        raw = self._try_all_methods(image)
        if not raw:
            # No detection → reset consecutive counter
            self._candidate_count = 0
            return

        code = self.normalise(raw)
        if not code:
            return

        now = time.time()

        # Consecutive-frame confirmation
        if code == self._candidate_code:
            self._candidate_count += 1
        else:
            self._candidate_code  = code
            self._candidate_count = 1

        if self._candidate_count < QR_CONFIRM_COUNT:
            return

        # Same-code cooldown
        if code == self._last_published_code:
            if now - self._last_publish_time < QR_COOLDOWN_S:
                return

        # Throttle any publish
        if now - self._last_publish_time < PUBLISH_THROTTLE_S:
            return

        self._last_published_code = code
        self._last_publish_time   = now

        msg = String()
        msg.data = code
        self.publisher_qr.publish(msg)
        self.get_logger().info(f'[QR] Published: {code}')

    # ── detection methods ─────────────────────────────────────────
    def _try_all_methods(self, image):
        """Try multiple backends / preprocessings; return first valid raw string."""
        # 1. pyzbar on colour image
        if PYZBAR_AVAILABLE:
            result = self._pyzbar_decode(image)
            if result:
                return result

        # 2. OpenCV detector on colour image
        result = self._opencv_decode(image)
        if result:
            return result

        # 3. pyzbar / OpenCV on preprocessed variants
        for prep in self._preprocessed_variants(image):
            if PYZBAR_AVAILABLE:
                result = self._pyzbar_decode(prep)
                if result:
                    return result
            result = self._opencv_decode(prep)
            if result:
                return result

        return None

    def _pyzbar_decode(self, image):
        try:
            objs = pyzbar.decode(image)
            for obj in objs:
                data = obj.data.decode('utf-8', errors='ignore').strip()
                if data:
                    return data
        except Exception:
            pass
        return None

    def _opencv_decode(self, image):
        try:
            data, bbox, _ = self._cv_detector.detectAndDecode(image)
            if bbox is not None and data:
                return data.strip()
        except Exception:
            pass
        return None

    def _preprocessed_variants(self, image):
        """Yield preprocessed images to improve detection reliability."""
        h, w = image.shape[:2]

        # Grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        yield gray

        # Upscaled (helps when QR is small)
        upscaled = cv2.resize(image, (w * 2, h * 2), interpolation=cv2.INTER_LINEAR)
        yield upscaled

        # CLAHE-enhanced
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        yield enhanced

        # Adaptive threshold (good for low-contrast scenes)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh  = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        yield thresh

        # Centre crop (buggy approaches building centre)
        cx, cy = w // 2, h // 2
        crop_w, crop_h = w * 3 // 4, h * 3 // 4
        x1 = max(cx - crop_w // 2, 0)
        y1 = max(cy - crop_h // 2, 0)
        cropped = image[y1:y1 + crop_h, x1:x1 + crop_w]
        if cropped.size > 0:
            yield cropped


def main(args=None):
    rclpy.init(args=args)
    node = QRDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
