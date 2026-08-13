"""
tflite_inference.py

Standalone inference engine for YOLOv11n TensorFlow Lite (FP32) models.
Designed strictly for NXP Cup India 2026 Evaluation Laptop deployment.
ONLY depends on:
    - tflite-runtime==2.14.0 (or fallback to ai_edge_litert / tensorflow.lite)
    - numpy
    - opencv-python (cv2)

Usage:
    python tflite_inference.py --model exports/best.tflite --image path/to/image.jpg
"""

import os
import sys
import time
import argparse
import cv2
import numpy as np

# Try importing TFLite interpreter with 3-tier fallback (tflite_runtime -> ai_edge_litert -> tf.lite)
try:
    from tflite_runtime.interpreter import Interpreter
    TFLITE_RUNTIME_SOURCE = "tflite_runtime.interpreter"
except ImportError:
    try:
        from ai_edge_litert.interpreter import Interpreter
        TFLITE_RUNTIME_SOURCE = "ai_edge_litert.interpreter"
    except ImportError:
        try:
            from tensorflow.lite import Interpreter
            TFLITE_RUNTIME_SOURCE = "tensorflow.lite"
        except ImportError:
            print("CRITICAL ERROR: No TFLite runtime found. Please install tflite-runtime==2.14.0.")
            sys.exit(1)


# Class mapping for Sign Board Detection Dataset (NXP Cup India 2026)
CLASS_NAMES = {
    0: 'A',
    1: 'B',
    2: 'C',
    3: 'Left',
    4: 'Right',
    5: 'Straight',
    6: 'X',
    7: 'Y',
    8: 'Z'
}


class TFLiteYOLOv11:
    """
    Lightweight, standalone TFLite inference class for YOLOv11 models.
    """
    def __init__(self, model_path: str, conf_thres: float = 0.25, iou_thres: float = 0.7):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"TFLite model file not found at: {model_path}")
        
        self.model_path = model_path
        self.conf_thres = conf_thres
        self.iou_thres = iou_thres
        
        # Initialize TFLite interpreter
        self.interpreter = Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()
            
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        self.in_idx = self.input_details[0]['index']
        self.out_idx = self.output_details[0]['index']
        self.in_shape = self.input_details[0]['shape']  # Expected: [1, 512, 512, 3]
        
    def letterbox(self, img: np.ndarray, new_shape=(512, 512), color=(114, 114, 114)):
        """Resize image preserving aspect ratio with gray padding."""
        shape = img.shape[:2]
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        
        dw, dh = (new_shape[1] - new_unpad[0]) / 2, (new_shape[0] - new_unpad[1]) / 2
        
        if shape[::-1] != new_unpad:
            img = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
            
        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        
        img = cv2.copyMakeBorder(img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        return img, r, (left, top)

    def predict(self, img_path: str):
        """Run inference on an image file and return detections dictionary."""
        img_bgr = cv2.imread(img_path)
        if img_bgr is None:
            raise ValueError(f"Could not read image: {img_path}")
            
        H, W = img_bgr.shape[:2]
        img_pad, r, (left, top) = self.letterbox(img_bgr, new_shape=(self.in_shape[1], self.in_shape[2]))
        
        # Preprocessing: BGR -> RGB, uint8 -> float32 [0.0, 1.0]
        inp = cv2.cvtColor(img_pad, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        inp = np.expand_dims(inp, axis=0)
        
        # Invoke interpreter
        t0 = time.perf_counter()
        self.interpreter.set_tensor(self.in_idx, inp)
        self.interpreter.invoke()
        t_infer = (time.perf_counter() - t0) * 1000.0  # ms
        
        # Postprocessing
        out_tensor = self.interpreter.get_tensor(self.out_idx)
        pred = out_tensor[0].T if out_tensor.shape[1] == 13 else out_tensor[0]
            
        boxes_xywh = pred[:, :4]
        scores_all = pred[:, 4:13]
        
        class_ids = np.argmax(scores_all, axis=1)
        max_scores = np.max(scores_all, axis=1)
        
        # Confidence filtering
        conf_mask = max_scores >= self.conf_thres
        boxes_xywh, max_scores, class_ids = boxes_xywh[conf_mask], max_scores[conf_mask], class_ids[conf_mask]
        
        if len(boxes_xywh) == 0:
            return {"boxes": [], "scores": [], "classes": [], "speed_ms": t_infer}
            
        # Convert center xywh to xyxy coordinates in original image space
        x1 = np.clip((boxes_xywh[:, 0] - boxes_xywh[:, 2]/2 - left) / r, 0, W)
        y1 = np.clip((boxes_xywh[:, 1] - boxes_xywh[:, 3]/2 - top) / r, 0, H)
        x2 = np.clip((boxes_xywh[:, 0] + boxes_xywh[:, 2]/2 - left) / r, 0, W)
        y2 = np.clip((boxes_xywh[:, 1] + boxes_xywh[:, 3]/2 - top) / r, 0, H)
        
        ltwh_boxes = [[x1[i], y1[i], x2[i] - x1[i], y2[i] - y1[i]] for i in range(len(x1))]
        
        # NMS
        nms_indices = cv2.dnn.NMSBoxes(ltwh_boxes, max_scores.tolist(), self.conf_thres, self.iou_thres)
        if len(nms_indices) > 0:
            nms_indices = nms_indices.flatten()
            final_boxes = np.stack([x1[nms_indices], y1[nms_indices], x2[nms_indices], y2[nms_indices]], axis=-1)
            final_scores = max_scores[nms_indices]
            final_classes = class_ids[nms_indices]
        else:
            final_boxes, final_scores, final_classes = [], [], []
            
        return {
            "boxes": final_boxes,
            "scores": final_scores,
            "classes": final_classes,
            "speed_ms": t_infer
        }


def main():
    parser = argparse.ArgumentParser(description="Standalone TFLite Inference for YOLOv11")
    parser.add_argument("--model", type=str, default="exports/best.tflite", help="Path to best.tflite model")
    parser.add_argument("--image", type=str, required=False, help="Path to test image")
    args = parser.parse_args()
    
    print(f"Initializing TFLite Runtime ({TFLITE_RUNTIME_SOURCE}) with model: {args.model}")
    engine = TFLiteYOLOv11(args.model)
    print("Model loaded successfully.")
    
    if args.image:
        print(f"Running inference on: {args.image}")
        res = engine.predict(args.image)
        print(f"Inference Time: {res['speed_ms']:.2f} ms")
        print(f"Detections Found: {len(res['boxes'])}")
        for i in range(len(res['boxes'])):
            cls_name = CLASS_NAMES.get(int(res['classes'][i]), str(res['classes'][i]))
            box = res['boxes'][i]
            print(f"  [{i+1}] Class: {cls_name:<8} Score: {res['scores'][i]:.4f}  Box: [{box[0]:.1f}, {box[1]:.1f}, {box[2]:.1f}, {box[3]:.1f}]")


if __name__ == "__main__":
    main()
