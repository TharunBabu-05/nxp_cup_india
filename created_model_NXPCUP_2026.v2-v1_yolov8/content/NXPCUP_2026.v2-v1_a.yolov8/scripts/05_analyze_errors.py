"""
scripts/05_analyze_errors.py
==============================
PHASE 7 — Model Error Analysis

Analyzes:
  - Per-class performance gaps
  - Confidence threshold sensitivity
  - Hard/confusing classes
  - False positive / false negative characteristics

Outputs:
  - results/confidence_sweep.png
  - results/error_analysis.png
  - reports/model_analysis.md
  - Optimization recommendations

Uses the test split predictions at multiple confidence thresholds
to find the optimal operating point.
"""

from __future__ import annotations

import json
import yaml
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_YAML    = PROJECT_ROOT / "data.yaml"
MODELS_DIR   = PROJECT_ROOT / "models"
RESULTS_DIR  = PROJECT_ROOT / "results"
REPORTS_DIR  = PROJECT_ROOT / "reports"
RUNS_DIR     = PROJECT_ROOT / "runs"
ABS_YAML     = PROJECT_ROOT / "configs" / "data_abs.yaml"


def load_class_names() -> list[str]:
    with open(DATA_YAML) as f:
        return yaml.safe_load(f)["names"]


def load_eval_metrics() -> dict:
    mp = RESULTS_DIR / "eval_metrics.json"
    if mp.exists():
        with open(mp) as f:
            return json.load(f)
    return {}


def find_best_model() -> Path:
    for c in [MODELS_DIR / "best.pt",
              *sorted(RUNS_DIR.glob("train/*/weights/best.pt"), reverse=True)]:
        if c.exists():
            return c
    raise FileNotFoundError("No best.pt found. Run 03_train.py first.")


def resolve_abs_yaml() -> Path:
    if ABS_YAML.exists():
        return ABS_YAML
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

    abs_cfg = {k: to_abs(cfg[k], k) if k in ("train", "val", "test") else cfg[k]
               for k in cfg}
    ABS_YAML.parent.mkdir(parents=True, exist_ok=True)
    with open(ABS_YAML, "w") as f:
        yaml.dump(abs_cfg, f, default_flow_style=False, sort_keys=False)
    return ABS_YAML


def confidence_sweep(model_path: Path, data_yaml: Path,
                     names: list[str]) -> tuple[list, list, list, list]:
    """Sweep conf thresholds from 0.1 to 0.9 and record mAP50/F1."""
    from ultralytics import YOLO
    import torch
    device = 0 if torch.cuda.is_available() else "cpu"
    model = YOLO(str(model_path))

    confs  = np.arange(0.05, 0.95, 0.05)
    map50s, precisions, recalls, f1s = [], [], [], []

    print("\n  Running confidence threshold sweep...")
    for conf in confs:
        res = model.val(
            data    = str(data_yaml),
            split   = "test",
            imgsz   = 512,
            batch   = 16,
            conf    = float(conf),
            iou     = 0.6,
            plots   = False,
            verbose = False,
            device  = device,
            save_json = False,
            project = str(RUNS_DIR / "eval" / "conf_sweep"),
            name    = f"conf_{conf:.2f}",
            exist_ok= True,
        )
        box = res.box
        p   = float(box.mp)
        r   = float(box.mr)
        f1  = 2 * p * r / max(p + r, 1e-6)
        map50s.append(float(box.map50))
        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)
        print(f"    conf={conf:.2f}  mAP50={box.map50:.4f}  P={p:.4f}  R={r:.4f}  F1={f1:.4f}")

    return list(confs), map50s, precisions, recalls, f1s


def plot_confidence_sweep(confs: list, map50s: list, precs: list,
                           recs: list, f1s: list) -> float:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(confs, map50s, "b-o", label="mAP50", linewidth=2)
    ax1.plot(confs, precs,  "g-s", label="Precision", linewidth=2)
    ax1.plot(confs, recs,   "r-^", label="Recall", linewidth=2)
    ax1.set_xlabel("Confidence Threshold")
    ax1.set_ylabel("Score")
    ax1.set_title("mAP50 / P / R vs Confidence", fontweight="bold")
    ax1.legend()
    ax1.grid(alpha=0.4)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1.05)

    best_idx  = int(np.argmax(f1s))
    best_conf = confs[best_idx]

    ax2.plot(confs, f1s, "m-D", linewidth=2, label="F1")
    ax2.axvline(best_conf, color="red", linestyle="--",
                label=f"Best conf={best_conf:.2f}  F1={f1s[best_idx]:.4f}")
    ax2.set_xlabel("Confidence Threshold")
    ax2.set_ylabel("F1 Score")
    ax2.set_title("F1 Score vs Confidence Threshold", fontweight="bold")
    ax2.legend()
    ax2.grid(alpha=0.4)
    ax2.set_xlim(0, 1)

    plt.suptitle("Confidence Threshold Analysis", fontsize=13, fontweight="bold")
    plt.tight_layout()

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "confidence_sweep.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  📊 confidence_sweep.png → {out}")
    return best_conf


def analyze_class_weaknesses(metrics: dict, names: list[str]) -> list[str]:
    """Return list of weak classes (AP50 < 0.70)."""
    pc   = metrics.get("per_class", {})
    weak = [n for n in names if pc.get(n, {}).get("ap50", 0) < 0.70]
    return weak


def write_analysis_report(metrics: dict, names: list[str],
                           best_conf: float, weak: list[str]) -> None:
    pc     = metrics.get("per_class", {})
    lines  = [
        "# Model Analysis Report — NXP Cup India 2026",
        "",
        "## Performance Summary",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| mAP50 | {metrics.get('mAP50', 0):.4f} |",
        f"| mAP50-95 | {metrics.get('mAP50_95', 0):.4f} |",
        f"| Best confidence threshold | {best_conf:.2f} |",
        "",
        "## Weak Classes (AP50 < 0.70)",
    ]
    if weak:
        for w in weak:
            d = pc.get(w, {})
            lines.append(f"- **{w}**: AP50={d.get('ap50',0):.4f}  "
                         f"P={d.get('precision',0):.4f}  R={d.get('recall',0):.4f}")
    else:
        lines.append("✅ All classes above 0.70 AP50 threshold.")

    # Recommendations
    lines += [
        "",
        "## Optimization Recommendations",
    ]

    overall_map = metrics.get("mAP50", 0)
    recs = []

    if weak:
        recs.append(f"- Oversample weak classes: {', '.join(weak)} "
                    f"(use `copy_paste=0.3` or online augmentation)")
    if overall_map < 0.80:
        recs.append("- Upgrade to **YOLOv8s** for higher capacity")
        recs.append("- Increase `epochs` to 200 with `patience=40`")
        recs.append("- Try `AdamW` optimizer: better for small datasets")
    if overall_map >= 0.90:
        recs.append("- Model is production-ready. Proceed to export.")
        recs.append("- Consider TensorRT FP16 export for edge deployment.")
    else:
        recs.append("- Apply test-time augmentation (TTA) for final eval")

    recs.append(f"- Use confidence threshold **{best_conf:.2f}** at inference")
    lines.extend(recs if recs else ["- No specific recommendations."])

    lines += [
        "",
        "## Next Step",
        "→ Phase 8: Model Optimization" if overall_map < 0.85
        else "→ Phase 9: Export (model is sufficiently accurate)",
        "",
        "*Generated by 05_analyze_errors.py*",
    ]

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "model_analysis.md"
    out.write_text("\n".join(lines))
    print(f"  📄 model_analysis.md → {out}")
    return recs


def main() -> None:
    print("\n" + "═"*60)
    print("  PHASE 7 — Model Error Analysis")
    print("═"*60)

    names      = load_class_names()
    metrics    = load_eval_metrics()
    model_path = find_best_model()
    data_yaml  = resolve_abs_yaml()

    if not metrics:
        print("  ⚠️  eval_metrics.json not found. Run 04_evaluate.py first.")
        return

    confs, map50s, precs, recs, f1s = confidence_sweep(
        model_path, data_yaml, names)
    best_conf = plot_confidence_sweep(confs, map50s, precs, recs, f1s)

    weak = analyze_class_weaknesses(metrics, names)
    if weak:
        print(f"\n  ⚠️  Weak classes detected: {weak}")
    else:
        print("\n  ✅ All classes above 0.70 AP50 threshold.")

    write_analysis_report(metrics, names, best_conf, weak)

    print(f"\n  Optimal confidence threshold: {best_conf:.2f}")
    print("\n" + "═"*60)
    print("  Phase 7 complete. Proceeding to Phase 8/9...")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
