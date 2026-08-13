"""
scripts/07_generate_report.py
================================
PHASE 12 — Project Report Generation

Aggregates all reports into a single PROJECT_REPORT.md.
Run after all other phases complete.
"""

from __future__ import annotations

import json
import yaml
from pathlib import Path
from datetime import datetime

SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
REPORTS_DIR  = PROJECT_ROOT / "reports"
RESULTS_DIR  = PROJECT_ROOT / "results"
MODELS_DIR   = PROJECT_ROOT / "models"
EXPORTS_DIR  = PROJECT_ROOT / "exports"
DATA_YAML    = PROJECT_ROOT / "data.yaml"


def load_json(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {}


def load_yaml_file(p: Path) -> dict:
    with open(p) as f:
        return yaml.safe_load(f)


def fmt_metric(v) -> str:
    try:
        return f"{float(v):.4f}"
    except Exception:
        return str(v)


def main() -> None:
    print("\n" + "═"*60)
    print("  PHASE 12 — Project Report Generation")
    print("═"*60)

    cfg     = load_yaml_file(DATA_YAML)
    metrics = load_json(RESULTS_DIR / "eval_metrics.json")

    # Model sizes
    def mb(p: Path) -> str:
        return f"{p.stat().st_size/1e6:.1f} MB" if p.exists() else "N/A"

    lines = [
        "# NXP Cup India 2026 — Project Report",
        f"\n*Generated: {datetime.now():%Y-%m-%d %H:%M:%S}*",
        "\n---",
        "\n## 1. Project Overview",
        "\n| Field | Value |",
        "|-------|-------|",
        "| Competition | NXP Cup India 2026 — Autonomous Medical Response Challenge |",
        "| Task | Sign board detection using YOLOv8 |",
        "| Framework | Ultralytics YOLOv8n |",
        "| OS | Ubuntu 22.04 |",
        "| Language | Python 3.10 |",
        "",
        "\n## 2. Dataset Summary",
        "\n| Metric | Value |",
        "|--------|-------|",
        f"| Total images | 2167 |",
        f"| Number of classes | {cfg.get('nc', 9)} |",
        f"| Class names | {', '.join(cfg.get('names', []))} |",
        f"| Image size | 512×512 |",
        f"| Format | YOLOv8 / Ultralytics |",
        f"| Augmentation | Crop, Shear, Brightness, Exposure, Blur, Salt+Pepper |",
        "",
        "\n## 3. Training Configuration",
        "\n| Parameter | Value |",
        "|-----------|-------|",
        "| Model | YOLOv8n (pretrained COCO) |",
        "| Epochs | 150 (early stop patience=30) |",
        "| Batch | 16 |",
        "| Image size | 512 |",
        "| Optimizer | SGD |",
        "| LR (initial) | 0.01 |",
        "| LR schedule | Cosine decay |",
        "| Augmentation | Mosaic, copy-paste, flip, HSV |",
        "",
        "\n## 4. Evaluation Results (Test Set)",
    ]

    if metrics:
        lines += [
            "\n| Metric | Value |",
            "|--------|-------|",
            f"| **mAP50** | **{fmt_metric(metrics.get('mAP50', 'N/A'))}** |",
            f"| mAP50-95 | {fmt_metric(metrics.get('mAP50_95', 'N/A'))} |",
            f"| Precision | {fmt_metric(metrics.get('precision', 'N/A'))} |",
            f"| Recall | {fmt_metric(metrics.get('recall', 'N/A'))} |",
            f"| F1 Score | {fmt_metric(metrics.get('f1', 'N/A'))} |",
            "",
            "\n### Per-class Metrics",
            "\n| Class | AP50 | AP50-95 | Precision | Recall | F1 |",
            "|-------|------|---------|-----------|--------|----|",
        ]
        pc = metrics.get("per_class", {})
        for name in cfg.get("names", []):
            d = pc.get(name, {})
            lines.append(
                f"| {name} | {fmt_metric(d.get('ap50',0))} | {fmt_metric(d.get('ap',0))} |"
                f" {fmt_metric(d.get('precision',0))} | {fmt_metric(d.get('recall',0))} |"
                f" {fmt_metric(d.get('f1',0))} |"
            )
    else:
        lines.append("\n*Evaluation not yet run. Execute 04_evaluate.py first.*")

    lines += [
        "",
        "\n## 5. Generated Artifacts",
        "\n| Artifact | Path | Status |",
        "|----------|------|--------|",
    ]

    artifacts = [
        ("Best model (.pt)",        MODELS_DIR / "best.pt"),
        ("Last model (.pt)",        MODELS_DIR / "last.pt"),
        ("ONNX model",              EXPORTS_DIR / "best.onnx"),
        ("TensorRT engine",         EXPORTS_DIR / "best.engine"),
        ("Confusion matrix",        RESULTS_DIR / "confusion_matrix.png"),
        ("PR curve",                RESULTS_DIR / "PR_curve.png"),
        ("F1 curve",                RESULTS_DIR / "F1_curve.png"),
        ("Confidence sweep",        RESULTS_DIR / "confidence_sweep.png"),
        ("Class distribution",      RESULTS_DIR / "class_distribution.png"),
        ("Dataset report",          REPORTS_DIR / "dataset_report.md"),
        ("Evaluation report",       REPORTS_DIR / "evaluation.md"),
        ("Model analysis",          REPORTS_DIR / "model_analysis.md"),
        ("Export report",           REPORTS_DIR / "export_report.md"),
        ("ROS2 integration guide",  PROJECT_ROOT / "docs" / "ros2_integration.md"),
    ]

    for label, path in artifacts:
        exists = "✅" if path.exists() else "⏳"
        size   = f" ({mb(path)})" if path.exists() and path.is_file() else ""
        lines.append(f"| {label} | `{path.name}` | {exists}{size} |")

    lines += [
        "",
        "\n## 6. Inference",
        "\n```bash",
        "# Single image",
        "python inference/inference.py --source path/to/image.jpg --conf 0.35",
        "",
        "# Folder of images",
        "python inference/inference.py --source path/to/folder/ --conf 0.35",
        "```",
        "",
        "\n## 7. ROS2 Deployment",
        "\nSee `docs/ros2_integration.md` for full integration guide.",
        "\nKey steps:",
        "1. Copy `models/best.pt` to your ROS2 package",
        "2. Update `MODEL_PATH` in `b3rb_ros_object_recog.py`",
        "3. Set `conf_thresh=0.35` as ROS2 parameter",
        "4. Subscribe to `/camera/image_compressed`",
        "5. Read sign class from `/sign_class` topic",
        "",
        "\n## 8. Recommendations",
        "",
        "- Use `conf=0.35` at inference (optimal from sweep analysis)",
        "- For embedded/Jetson deployment, use `exports/best.engine` (TensorRT FP16)",
        "- Monitor per-class AP during deployment — classes with lower AP may need post-processing",
        "- If mAP50 < 0.85 after training, consider upgrading to YOLOv8s",
        "",
        "\n## 9. Future Improvements",
        "",
        "- [ ] Add video stream inference support",
        "- [ ] Add distance estimation via bounding box size",
        "- [ ] Train YOLOv8s for higher accuracy if needed",
        "- [ ] Implement temporal smoothing in ROS2 node",
        "- [ ] Add multi-class NMS for overlapping signs",
        "",
        "\n---",
        "*NXP Cup India 2026 — Auto-generated by 07_generate_report.py*",
    ]

    out = PROJECT_ROOT / "PROJECT_REPORT.md"
    out.write_text("\n".join(lines))
    print(f"\n  📄 PROJECT_REPORT.md → {out}")
    print("\n" + "═"*60)
    print("  Phase 12 complete. Pipeline finished!")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
