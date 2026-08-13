"""
scripts/03_train.py
=====================
PHASE 4 + 5 — Training Plan & Training Execution

Responsibilities:
  - Resolve absolute paths for data.yaml (avoids relative-path issues)
  - Load training_config.yaml
  - Launch YOLOv8n training with full monitoring
  - Handle resume on crash
  - Save model artifacts to models/
  - Log training summary to logs/training.log

Design decision: YOLOv8n chosen because:
  - Sign board detection requires speed over brute accuracy
  - ROS2 embedded deployment requires small model footprint
  - Dataset is 2167 images — nano is sufficient for convergence
  - Upgrade to yolov8s only if mAP50 < 0.80 post-training
"""

from __future__ import annotations

import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime

import yaml

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_YAML    = PROJECT_ROOT / "data.yaml"
CONFIG_YAML  = PROJECT_ROOT / "configs" / "training_config.yaml"
MODELS_DIR   = PROJECT_ROOT / "models"
LOGS_DIR     = PROJECT_ROOT / "logs"
RUNS_DIR     = PROJECT_ROOT / "runs"


# ── Logging ────────────────────────────────────────────────────────────────────
def setup_logger() -> logging.Logger:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"training_{datetime.now():%Y%m%d_%H%M%S}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logger = logging.getLogger("nxpcup.train")
    logger.info(f"Log file: {log_file}")
    return logger


# ── Config resolution ──────────────────────────────────────────────────────────
def resolve_data_yaml() -> Path:
    """
    YOLOv8 resolves paths relative to the yaml location.
    Write a temp data.yaml with absolute paths to avoid ambiguity.
    """
    with open(DATA_YAML) as f:
        cfg = yaml.safe_load(f)

    def to_abs(raw: str, key: str) -> str:
        p = Path(raw)
        if p.is_absolute() and p.exists():
            return str(p)
        cand1 = (DATA_YAML.parent / p).resolve()
        if cand1.exists():
            return str(cand1)
        clean_raw = raw.lstrip('./').lstrip('../')
        cand2 = (DATA_YAML.parent / clean_raw).resolve()
        if cand2.exists():
            return str(cand2)
        alias = "valid" if key == "val" else key
        cand3 = (DATA_YAML.parent / alias / "images").resolve()
        if cand3.exists():
            return str(cand3)
        return str(cand1)

    abs_cfg = {
        "train": to_abs(cfg["train"], "train"),
        "val":   to_abs(cfg["val"], "val"),
        "test":  to_abs(cfg["test"], "test"),
        "nc":    cfg["nc"],
        "names": cfg["names"],
    }

    abs_yaml = PROJECT_ROOT / "configs" / "data_abs.yaml"
    abs_yaml.parent.mkdir(parents=True, exist_ok=True)
    with open(abs_yaml, "w") as f:
        yaml.dump(abs_cfg, f, default_flow_style=False, sort_keys=False)

    return abs_yaml


def load_train_config() -> dict:
    with open(CONFIG_YAML) as f:
        return yaml.safe_load(f)


# ── Detect previous run for resume ────────────────────────────────────────────
def find_last_checkpoint() -> Path | None:
    run_dir = RUNS_DIR / "train"
    if not run_dir.exists():
        return None
    # Look for the most recent run with a last.pt
    runs = sorted(run_dir.iterdir(), reverse=True)
    for r in runs:
        lp = r / "weights" / "last.pt"
        if lp.exists():
            return lp
    return None


# ── Training ──────────────────────────────────────────────────────────────────
def train(logger: logging.Logger) -> Path:
    from ultralytics import YOLO

    tcfg     = load_train_config()
    data_abs = resolve_data_yaml()

    logger.info("=" * 60)
    logger.info("  NXP Cup India 2026 — YOLOv8n Training")
    logger.info("=" * 60)
    logger.info(f"  Data YAML   : {data_abs}")
    logger.info(f"  Config      : {CONFIG_YAML}")
    logger.info(f"  Model       : {tcfg['model']}")
    logger.info(f"  Epochs      : {tcfg['epochs']}")
    logger.info(f"  Batch       : {tcfg['batch']}")
    logger.info(f"  Image size  : {tcfg['imgsz']}")
    logger.info(f"  Optimizer   : {tcfg['optimizer']}")

    # Check for existing checkpoint to resume
    last_ckpt = find_last_checkpoint()
    if last_ckpt:
        logger.info(f"  Resuming from checkpoint: {last_ckpt}")
        model = YOLO(str(last_ckpt))
        resume = True
    else:
        logger.info(f"  Starting fresh from: {tcfg['model']}")
        model = YOLO(tcfg["model"])
        resume = False

    import torch
    device = tcfg["device"]
    if not torch.cuda.is_available():
        logger.warning("CUDA unavailable — falling back to device='cpu'")
        device = "cpu"

    # Build training kwargs from config
    train_kwargs = dict(
        data        = str(data_abs),
        epochs      = tcfg["epochs"],
        patience    = tcfg["patience"],
        batch       = tcfg["batch"],
        imgsz       = tcfg["imgsz"],
        device      = device,
        optimizer   = tcfg["optimizer"],
        lr0         = tcfg["lr0"],
        lrf         = tcfg["lrf"],
        momentum    = tcfg["momentum"],
        weight_decay= tcfg["weight_decay"],
        warmup_epochs      = tcfg["warmup_epochs"],
        warmup_momentum    = tcfg["warmup_momentum"],
        warmup_bias_lr     = tcfg["warmup_bias_lr"],
        box         = tcfg["box"],
        cls         = tcfg["cls"],
        dfl         = tcfg["dfl"],
        mosaic      = tcfg["mosaic"],
        mixup       = tcfg["mixup"],
        degrees     = tcfg["degrees"],
        translate   = tcfg["translate"],
        scale       = tcfg["scale"],
        shear       = tcfg["shear"],
        perspective = tcfg["perspective"],
        flipud      = tcfg["flipud"],
        fliplr      = tcfg["fliplr"],
        hsv_h       = tcfg["hsv_h"],
        hsv_s       = tcfg["hsv_s"],
        hsv_v       = tcfg["hsv_v"],
        erasing     = tcfg["erasing"],
        copy_paste  = tcfg["copy_paste"],
        project     = str(RUNS_DIR / "train"),
        name        = tcfg["name"],
        exist_ok    = True,          # allow resume writes
        save        = tcfg["save"],
        save_period = tcfg["save_period"],
        plots       = tcfg["plots"],
        verbose     = tcfg["verbose"],
        workers     = tcfg["workers"],
        val         = tcfg["val"],
        resume      = resume,
    )

    logger.info("  Launching training...")
    results = model.train(**train_kwargs)
    logger.info("  Training complete!")

    # Copy best/last weights to models/
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = Path(results.save_dir)
    for wname in ["best.pt", "last.pt"]:
        src = run_dir / "weights" / wname
        dst = MODELS_DIR / wname
        if src.exists():
            shutil.copy2(src, dst)
            logger.info(f"  Saved {wname} → {dst}")
        else:
            logger.warning(f"  {wname} not found at {src}")

    logger.info(f"\n  ✅ Artifacts saved to: {MODELS_DIR}")
    logger.info(f"  ✅ Run directory     : {run_dir}")
    return run_dir


def main() -> None:
    logger = setup_logger()
    try:
        run_dir = train(logger)
        logger.info(f"\n  Training finished. Run dir: {run_dir}")
        logger.info("  Proceeding to Phase 6 — Evaluation...")
    except KeyboardInterrupt:
        logger.warning("\n  Training interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n  Training failed with error: {e}", exc_info=True)
        logger.error("  Check the log file and resolve the issue.")
        sys.exit(1)


if __name__ == "__main__":
    main()
