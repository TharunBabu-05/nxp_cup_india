"""
scripts/04_evaluate.py
========================
PHASE 6 — Model Evaluation on Test Dataset

Evaluates best.pt on the test split.

Metrics computed:
  - Precision, Recall, F1 per class
  - mAP50, mAP50-95 per class and overall
  - Confusion Matrix
  - PR Curve, F1 Curve, P Curve, R Curve

Outputs:
  - results/eval_metrics.json
  - results/confusion_matrix.png (regenerated explicitly)
  - results/pr_curve.png
  - results/f1_curve.png
  - reports/evaluation.md
"""

from __future__ import annotations

import json
import shutil
import yaml
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_YAML    = PROJECT_ROOT / "data.yaml"
MODELS_DIR   = PROJECT_ROOT / "models"
RESULTS_DIR  = PROJECT_ROOT / "results"
REPORTS_DIR  = PROJECT_ROOT / "reports"
RUNS_DIR     = PROJECT_ROOT / "runs"
ABS_YAML     = PROJECT_ROOT / "configs" / "data_abs.yaml"


def resolve_data_yaml() -> Path:
    """Ensure absolute-path yaml exists."""
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
    ABS_YAML.parent.mkdir(parents=True, exist_ok=True)
    with open(ABS_YAML, "w") as f:
        yaml.dump(abs_cfg, f, default_flow_style=False, sort_keys=False)
    return ABS_YAML


def load_class_names() -> list[str]:
    with open(DATA_YAML) as f:
        return yaml.safe_load(f)["names"]


def find_best_model() -> Path:
    # Priority: models/best.pt > latest run weights
    candidates = [
        MODELS_DIR / "best.pt",
        *sorted(RUNS_DIR.glob("train/*/weights/best.pt"), reverse=True),
    ]
    for c in candidates:
        if c.exists():
            print(f"  Using model: {c}")
            return c
    raise FileNotFoundError(
        "No best.pt found. Run 03_train.py first."
    )


def run_val(model_path: Path, data_yaml: Path, split: str = "test") -> object:
    from ultralytics import YOLO
    import torch
    device = 0 if torch.cuda.is_available() else "cpu"
    model = YOLO(str(model_path))
    results = model.val(
        data    = str(data_yaml),
        split   = split,
        imgsz   = 512,
        batch   = 16,
        device  = device,
        conf    = 0.001,      # low conf to build full PR curve
        iou     = 0.6,
        plots   = True,
        save_json = False,
        project = str(RUNS_DIR / "eval"),
        name    = f"test_{datetime.now():%Y%m%d_%H%M%S}",
        verbose = True,
    )
    return results


def extract_metrics(results, names: list[str]) -> dict:
    """Extract structured metrics from Ultralytics results object."""
    box = results.box

    metrics = {
        "mAP50"    : float(box.map50),
        "mAP50_95" : float(box.map),
        "precision": float(box.mp),
        "recall"   : float(box.mr),
        "f1"       : float(2 * box.mp * box.mr / max(box.mp + box.mr, 1e-6)),
    }

    # Per-class metrics
    per_class = {}
    for i, name in enumerate(names):
        try:
            ap50    = float(box.ap50[i])  if hasattr(box, "ap50")  else 0.0
            ap      = float(box.ap[i])    if hasattr(box, "ap")    else 0.0
            prec    = float(box.p[i])     if hasattr(box, "p")     else 0.0
            rec     = float(box.r[i])     if hasattr(box, "r")     else 0.0
            f1_val  = 2 * prec * rec / max(prec + rec, 1e-6)
            per_class[name] = dict(
                ap50=round(ap50, 4), ap=round(ap, 4),
                precision=round(prec, 4), recall=round(rec, 4),
                f1=round(f1_val, 4),
            )
        except (IndexError, AttributeError):
            per_class[name] = dict(ap50=0, ap=0, precision=0, recall=0, f1=0)

    metrics["per_class"] = per_class
    return metrics


def save_metrics(metrics: dict) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "eval_metrics.json"
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  📄 eval_metrics.json → {out}")


def copy_eval_plots(eval_run_dir: Path) -> None:
    """Copy confusion matrix and curves from ultralytics eval run dir."""
    plot_names = [
        "confusion_matrix.png",
        "confusion_matrix_normalized.png",
        "PR_curve.png",
        "F1_curve.png",
        "P_curve.png",
        "R_curve.png",
        "results.png",
    ]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for pname in plot_names:
        src = eval_run_dir / pname
        if src.exists():
            dst = RESULTS_DIR / pname
            shutil.copy2(src, dst)
            print(f"  📊 {pname} → {dst}")
        else:
            print(f"  ⚠️  {pname} not found in {eval_run_dir}")


def plot_per_class_ap(metrics: dict, names: list[str]) -> None:
    pc = metrics.get("per_class", {})
    ap50s = [pc.get(n, {}).get("ap50", 0) for n in names]
    f1s   = [pc.get(n, {}).get("f1", 0)   for n in names]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    colors = plt.cm.tab10(np.linspace(0, 1, len(names)))

    ax1.barh(names, ap50s, color=colors, edgecolor="black", linewidth=0.6)
    ax1.set_xlim(0, 1.05)
    ax1.set_title("Per-class AP50", fontsize=12, fontweight="bold")
    ax1.set_xlabel("AP50")
    ax1.axvline(metrics["mAP50"], color="red", linestyle="--", linewidth=1.5,
                label=f"mAP50={metrics['mAP50']:.3f}")
    ax1.legend()
    ax1.grid(axis="x", alpha=0.4)
    for i, v in enumerate(ap50s):
        ax1.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=8)

    ax2.barh(names, f1s, color=colors, edgecolor="black", linewidth=0.6)
    ax2.set_xlim(0, 1.05)
    ax2.set_title("Per-class F1 Score", fontsize=12, fontweight="bold")
    ax2.set_xlabel("F1")
    ax2.axvline(metrics["f1"], color="red", linestyle="--", linewidth=1.5,
                label=f"Overall F1={metrics['f1']:.3f}")
    ax2.legend()
    ax2.grid(axis="x", alpha=0.4)
    for i, v in enumerate(f1s):
        ax2.text(v + 0.01, i, f"{v:.3f}", va="center", fontsize=8)

    plt.suptitle("Per-class Performance — Test Set", fontsize=13, fontweight="bold")
    plt.tight_layout()
    out = RESULTS_DIR / "per_class_ap.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  📊 per_class_ap.png → {out}")


def write_evaluation_report(metrics: dict, names: list[str]) -> None:
    pc    = metrics.get("per_class", {})
    lines = [
        "# Evaluation Report — NXP Cup India 2026",
        f"\n*Evaluated: {datetime.now():%Y-%m-%d %H:%M:%S}*",
        "\n## Overall Metrics (Test Set)",
        "\n| Metric | Value |",
        "|--------|-------|",
        f"| mAP50       | {metrics['mAP50']:.4f} |",
        f"| mAP50-95    | {metrics['mAP50_95']:.4f} |",
        f"| Precision   | {metrics['precision']:.4f} |",
        f"| Recall      | {metrics['recall']:.4f} |",
        f"| F1 Score    | {metrics['f1']:.4f} |",
        "\n## Per-class Metrics",
        "\n| Class | AP50 | AP50-95 | Precision | Recall | F1 |",
        "|-------|------|---------|-----------|--------|----|",
    ]
    for name in names:
        d = pc.get(name, {})
        lines.append(
            f"| {name} | {d.get('ap50',0):.4f} | {d.get('ap',0):.4f} |"
            f" {d.get('precision',0):.4f} | {d.get('recall',0):.4f} | {d.get('f1',0):.4f} |"
        )

    verdict = "🟢 EXCELLENT" if metrics["mAP50"] >= 0.90 else \
              "🟡 GOOD"     if metrics["mAP50"] >= 0.80 else \
              "🔴 NEEDS IMPROVEMENT"

    lines += [
        f"\n## Verdict: {verdict}",
        "",
        "| Threshold | mAP50 Target | Status |",
        "|-----------|-------------|--------|",
        f"| Excellent | ≥ 0.90 | {'✅' if metrics['mAP50'] >= 0.90 else '❌'} |",
        f"| Good      | ≥ 0.80 | {'✅' if metrics['mAP50'] >= 0.80 else '❌'} |",
        f"| Minimum   | ≥ 0.70 | {'✅' if metrics['mAP50'] >= 0.70 else '❌'} |",
        "\n## Generated Artifacts",
        "- `results/confusion_matrix.png`",
        "- `results/confusion_matrix_normalized.png`",
        "- `results/PR_curve.png`",
        "- `results/F1_curve.png`",
        "- `results/per_class_ap.png`",
        "- `results/eval_metrics.json`",
        "\n*Generated by 04_evaluate.py*",
    ]
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "evaluation.md"
    out.write_text("\n".join(lines))
    print(f"  📄 evaluation.md → {out}")


def main() -> None:
    print("\n" + "═"*60)
    print("  PHASE 6 — Model Evaluation on Test Set")
    print("═"*60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    names      = load_class_names()
    data_yaml  = resolve_data_yaml()
    model_path = find_best_model()

    print(f"\n  Evaluating {model_path.name} on test split...")
    results = run_val(model_path, data_yaml, split="test")

    metrics = extract_metrics(results, names)
    save_metrics(metrics)

    # Copy plots generated by ultralytics
    eval_run_dir = Path(results.save_dir)
    copy_eval_plots(eval_run_dir)

    plot_per_class_ap(metrics, names)
    write_evaluation_report(metrics, names)

    print("\n  ── Summary ──────────────────────────────")
    print(f"  mAP50     : {metrics['mAP50']:.4f}")
    print(f"  mAP50-95  : {metrics['mAP50_95']:.4f}")
    print(f"  Precision : {metrics['precision']:.4f}")
    print(f"  Recall    : {metrics['recall']:.4f}")
    print(f"  F1        : {metrics['f1']:.4f}")
    print("\n" + "═"*60)
    print("  Phase 6 complete. Proceeding to Phase 7...")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
