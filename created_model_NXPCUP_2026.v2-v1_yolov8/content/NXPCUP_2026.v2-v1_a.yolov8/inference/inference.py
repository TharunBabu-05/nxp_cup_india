"""
inference/inference.py
========================
PHASE 10 — Inference Script

Usage:
  python inference/inference.py --source <image_or_folder_or_video>

Arguments:
  --source  : Path to image file, folder of images, or video
  --model   : Path to model weights (default: models/best.pt)
  --conf    : Confidence threshold (default: 0.35)
  --iou     : IOU threshold (default: 0.6)
  --device  : Device (0 = GPU, cpu)
  --output  : Output directory (default: results/inference)
  --save    : Save output images/video
  --show    : Show detections in window (requires display)
  --nosave  : Skip saving output

Outputs:
  - Annotated image(s) saved to results/inference/
  - Per-image JSON with class, confidence, bounding box
  - Console summary per image

Designed for integration with b3rb_ros_object_recog.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
MODELS_DIR   = PROJECT_ROOT / "models"
RESULTS_DIR  = PROJECT_ROOT / "results" / "inference"

CLASS_NAMES = ["A", "B", "C", "Left", "Right", "Straight", "X", "Y", "Z"]

# Color palette per class (BGR for OpenCV)
PALETTE = [
    (255,  56,  56),   # A     — red
    (255, 157,  51),   # B     — orange
    (255, 178, 179),   # C     — pink
    ( 46, 196, 182),   # Left  — teal
    ( 60, 220, 205),   # Right — cyan
    ( 63, 200, 255),   # Straight — sky
    (152,  57, 189),   # X     — purple
    ( 56, 200, 107),   # Y     — green
    (255, 255,  52),   # Z     — yellow
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="NXP Cup India 2026 — YOLOv8 Inference",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--source",  required=True, help="Image path, folder, or video")
    p.add_argument("--model",   default=str(MODELS_DIR / "best.pt"), help="Model weights")
    p.add_argument("--conf",    type=float, default=0.35,  help="Confidence threshold")
    p.add_argument("--iou",     type=float, default=0.60,  help="IoU NMS threshold")
    p.add_argument("--device",  default="0",  help="Device: 0 (GPU) or cpu")
    p.add_argument("--imgsz",   type=int, default=512, help="Inference image size")
    p.add_argument("--output",  default=str(RESULTS_DIR), help="Output directory")
    p.add_argument("--save",    action="store_true", default=True)
    p.add_argument("--nosave",  action="store_true", default=False)
    p.add_argument("--show",    action="store_true", default=False)
    return p.parse_args()


def load_model(model_path: str, device: str):
    """Load YOLOv8 model."""
    from ultralytics import YOLO
    import torch
    path = Path(model_path)
    if not path.exists():
        print(f"❌ Model not found: {path}")
        sys.exit(1)
    print(f"  Loading model: {path.name}")
    return YOLO(str(path))


def draw_detections(frame: np.ndarray, boxes, conf_thresh: float) -> tuple[np.ndarray, list]:
    """
    Draw bounding boxes on frame.

    Returns:
        annotated frame, list of detection dicts
    """
    annotated = frame.copy()
    detections = []

    if boxes is None or len(boxes) == 0:
        return annotated, detections

    for box in boxes:
        conf = float(box.conf[0])
        if conf < conf_thresh:
            continue

        cls_id = int(box.cls[0])
        cls_name = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else str(cls_id)
        color = PALETTE[cls_id % len(PALETTE)]

        # Bounding box in xyxy pixel coords
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Draw box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

        # Label background
        label     = f"{cls_name} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(annotated, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
        cv2.putText(annotated, label, (x1 + 2, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

        # Normalised xywh for output
        h, w = frame.shape[:2]
        cx   = ((x1 + x2) / 2) / w
        cy   = ((y1 + y2) / 2) / h
        bw   = (x2 - x1) / w
        bh   = (y2 - y1) / h

        detections.append({
            "class_id"  : cls_id,
            "class_name": cls_name,
            "confidence": round(conf, 4),
            "bbox_xyxy" : [x1, y1, x2, y2],
            "bbox_xywh_norm": [round(cx, 4), round(cy, 4), round(bw, 4), round(bh, 4)],
        })

    return annotated, detections


def run_inference_image(model, img_path: Path, args: argparse.Namespace) -> list:
    """Run inference on a single image."""
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"  ⚠️  Cannot read: {img_path}")
        return []

    import torch
    dev = args.device if (args.device != "0" or torch.cuda.is_available()) else "cpu"
    t0  = time.perf_counter()
    res = model.predict(
        source  = img,
        conf    = args.conf,
        iou     = args.iou,
        device  = dev,
        imgsz   = args.imgsz,
        verbose = False,
    )
    dt = (time.perf_counter() - t0) * 1000

    boxes       = res[0].boxes
    annotated, detections = draw_detections(img, boxes, args.conf)

    # Console output
    print(f"\n  [{img_path.name}]  {dt:.1f} ms  —  {len(detections)} detection(s)")
    for d in detections:
        print(f"    · {d['class_name']:<12} conf={d['confidence']:.4f}  "
              f"bbox={d['bbox_xyxy']}")

    out_dir = Path(args.output)
    if args.save and not args.nosave:
        out_dir.mkdir(parents=True, exist_ok=True)
        out_img  = out_dir / img_path.name
        out_json = out_dir / (img_path.stem + "_detections.json")
        cv2.imwrite(str(out_img), annotated)
        with open(out_json, "w") as f:
            json.dump({"image": str(img_path), "detections": detections,
                       "inference_ms": round(dt, 2)}, f, indent=2)
        print(f"    Saved → {out_img}")

    if args.show:
        cv2.imshow("NXP Cup Inference", annotated)
        cv2.waitKey(1)

    return detections


def main() -> None:
    print("\n" + "═"*60)
    print("  NXP Cup India 2026 — YOLOv8 Inference")
    print("═"*60)

    args  = parse_args()
    model = load_model(args.model, args.device)
    src   = Path(args.source)

    if not src.exists():
        print(f"❌ Source not found: {src}")
        sys.exit(1)

    # Collect targets
    if src.is_file():
        targets = [src]
    elif src.is_dir():
        exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
        targets = sorted(f for f in src.iterdir() if f.suffix.lower() in exts)
        print(f"  Found {len(targets)} images in {src}")
    else:
        print(f"❌ Source must be a file or directory: {src}")
        sys.exit(1)

    all_detections = []
    for target in targets:
        dets = run_inference_image(model, target, args)
        all_detections.extend(dets)

    # Summary
    print(f"\n{'─'*60}")
    print(f"  Processed : {len(targets)} image(s)")
    print(f"  Total detections : {len(all_detections)}")
    if all_detections:
        from collections import Counter
        counts = Counter(d["class_name"] for d in all_detections)
        print(f"  Per-class counts:")
        for cls, cnt in sorted(counts.items()):
            print(f"    {cls:<12}: {cnt}")
    print(f"  Output saved to : {args.output}")
    print("═"*60 + "\n")

    if args.show:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
