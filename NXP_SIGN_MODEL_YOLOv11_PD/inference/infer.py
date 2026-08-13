#!/usr/bin/env python3
"""Run inference with the trained NXP CUP YOLOv11n sign detector."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils import detect_device, setup_logging

logger = setup_logging("infer")


def parse_args(argv: Optional[list] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Infer with YOLOv11n road-sign detector")
    p.add_argument("--weights", type=str, default=str(PROJECT_ROOT / "exports" / "best.pt"))
    p.add_argument("--source", type=str, required=True, help="Image, directory, or video path")
    p.add_argument("--imgsz", type=int, default=512)
    p.add_argument("--conf", type=float, default=0.25)
    p.add_argument("--iou", type=float, default=0.45)
    p.add_argument("--device", type=str, default=None)
    p.add_argument("--project", type=str, default=str(PROJECT_ROOT / "runs" / "predict"))
    p.add_argument("--name", type=str, default="nxp_signs")
    p.add_argument("--save-txt", action="store_true")
    p.add_argument("--save-conf", action="store_true")
    return p.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = parse_args(argv)
    from ultralytics import YOLO

    weights = Path(args.weights)
    if not weights.is_absolute():
        weights = PROJECT_ROOT / weights
    if not weights.exists():
        logger.error("Weights not found: %s", weights)
        return 1

    device = detect_device(args.device)
    model = YOLO(str(weights))
    results = model.predict(
        source=args.source,
        imgsz=args.imgsz,
        conf=args.conf,
        iou=args.iou,
        device=device,
        project=args.project,
        name=args.name,
        exist_ok=True,
        save=True,
        save_txt=args.save_txt,
        save_conf=args.save_conf,
    )
    logger.info("Processed %d source(s). Outputs under %s/%s", len(results), args.project, args.name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
