"""
scripts/02_dataset_analysis.py
================================
PHASE 3 — Dataset Analysis & Visualization

Generates:
  - Class distribution bar chart
  - Bounding box size distribution
  - Aspect ratio distribution
  - Sample image grid with annotations
  - reports/dataset_analysis.md

Never modifies the dataset.
"""

from __future__ import annotations

import random
import yaml
import collections
import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless rendering
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path
from PIL import Image

# ── Paths ─────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_YAML    = PROJECT_ROOT / "data.yaml"
REPORTS_DIR  = PROJECT_ROOT / "reports"
RESULTS_DIR  = PROJECT_ROOT / "results"
SUPPORTED    = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_yaml() -> dict:
    with open(DATA_YAML) as f:
        return yaml.safe_load(f)


def resolve(raw: str, key: str = "") -> Path:
    p = Path(raw)
    if p.is_absolute() and p.exists():
        return p
    cand1 = (DATA_YAML.parent / p).resolve()
    if cand1.exists():
        return cand1
    clean_raw = raw.lstrip('./').lstrip('../')
    cand2 = (DATA_YAML.parent / clean_raw).resolve()
    if cand2.exists():
        return cand2
    alias = "valid" if key == "val" else key
    cand3 = (DATA_YAML.parent / alias / "images").resolve()
    if cand3.exists():
        return cand3
    return cand1


def gather_all_labels(cfg: dict) -> tuple[list, list, list, list]:
    """Return class_ids, cx_cy_wh lists, img_sizes, split_tags."""
    class_ids, boxes, img_sizes, tags = [], [], [], []
    splits = {
        "train": resolve(cfg["train"], "train"),
        "valid": resolve(cfg["val"], "val"),
        "test":  resolve(cfg["test"], "test"),
    }
    for tag, img_dir in splits.items():
        lbl_dir = img_dir.parent / "labels"
        if not lbl_dir.exists():
            continue
        for lf in lbl_dir.iterdir():
            if lf.suffix != ".txt":
                continue
            # find matching image
            img_path = None
            for ext in SUPPORTED:
                candidate = img_dir / (lf.stem + ext)
                if candidate.exists():
                    img_path = candidate
                    break

            if img_path:
                try:
                    with Image.open(img_path) as im:
                        img_sizes.append(im.size)  # (W, H)
                except Exception:
                    pass

            for line in lf.read_text().splitlines():
                parts = line.strip().split()
                if len(parts) == 5:
                    try:
                        cid = int(parts[0])
                        cx, cy, w, h = map(float, parts[1:])
                        class_ids.append(cid)
                        boxes.append((cx, cy, w, h))
                        tags.append(tag)
                    except ValueError:
                        pass
    return class_ids, boxes, img_sizes, tags


def plot_class_distribution(class_ids: list, names: list) -> Path:
    counter = collections.Counter(class_ids)
    labels  = [names[i] if i < len(names) else str(i) for i in sorted(counter)]
    counts  = [counter[i] for i in sorted(counter)]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = plt.cm.tab10(np.linspace(0, 1, len(labels)))
    bars = ax.bar(labels, counts, color=colors, edgecolor="black", linewidth=0.7)

    for bar, cnt in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
                str(cnt), ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_title("Class Distribution — NXP Cup India 2026", fontsize=14, fontweight="bold")
    ax.set_xlabel("Class")
    ax.set_ylabel("Annotation Count")
    ax.set_ylim(0, max(counts) * 1.15)
    ax.grid(axis="y", alpha=0.4)
    plt.tight_layout()

    out = RESULTS_DIR / "class_distribution.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  📊 class_distribution.png → {out}")
    return out


def plot_bbox_stats(boxes: list) -> Path:
    ws = [b[2] for b in boxes]
    hs = [b[3] for b in boxes]
    areas = [w * h for w, h in zip(ws, hs)]
    aspects = [w / max(h, 1e-6) for w, h in zip(ws, hs)]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, data, title, xlabel in zip(
        axes,
        [ws, hs, areas],
        ["Bounding Box Width (norm)", "Bounding Box Height (norm)", "Bounding Box Area (norm)"],
        ["Width", "Height", "Area"],
    ):
        ax.hist(data, bins=50, color="steelblue", edgecolor="black", linewidth=0.5, alpha=0.85)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Frequency")
        ax.grid(alpha=0.3)

    plt.suptitle("Bounding Box Statistics", fontsize=13, fontweight="bold")
    plt.tight_layout()
    out = RESULTS_DIR / "bbox_stats.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"  📊 bbox_stats.png → {out}")
    return out


def plot_sample_grid(cfg: dict) -> Path:
    """Draw 16 random annotated sample images in a 4×4 grid."""
    names  = cfg["names"]
    colors = plt.cm.tab10(np.linspace(0, 1, len(names)))

    img_dir = resolve(cfg["train"], "train")
    lbl_dir = img_dir.parent / "labels"

    pairs = []
    for lf in lbl_dir.iterdir():
        if lf.suffix != ".txt":
            continue
        for ext in SUPPORTED:
            ip = img_dir / (lf.stem + ext)
            if ip.exists():
                pairs.append((ip, lf))
                break

    if not pairs:
        print("  ⚠️  No image-label pairs found for sample grid — skipping")
        out = RESULTS_DIR / "sample_grid.png"
        fig, ax = plt.subplots(1, 1, figsize=(4, 4))
        ax.text(0.5, 0.5, "No samples found", ha="center", va="center")
        ax.axis("off")
        fig.savefig(out, dpi=100)
        plt.close(fig)
        return out

    random.seed(42)
    chosen = random.sample(pairs, min(16, len(pairs)))
    n_cols = 4
    n_rows = (len(chosen) + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, n_rows * 4))
    axes = np.array(axes).flatten()

    for ax, (ip, lf) in zip(axes, chosen):
        img = Image.open(ip).convert("RGB")
        W, H = img.size
        ax.imshow(img)
        for line in lf.read_text().splitlines():
            parts = line.strip().split()
            if len(parts) == 5:
                try:
                    cid = int(parts[0])
                    cx, cy, bw, bh = map(float, parts[1:])
                    x = (cx - bw / 2) * W
                    y = (cy - bh / 2) * H
                    w = bw * W
                    h = bh * H
                    color = colors[cid % len(colors)]
                    rect = patches.Rectangle((x, y), w, h,
                                             linewidth=2, edgecolor=color, facecolor="none")
                    ax.add_patch(rect)
                    label = names[cid] if cid < len(names) else str(cid)
                    ax.text(x, y - 4, label, fontsize=7, color=color, fontweight="bold",
                            bbox=dict(facecolor="black", alpha=0.4, pad=1))
                except (ValueError, IndexError):
                    pass
        ax.set_title(ip.name[:20], fontsize=7)
        ax.axis("off")

    for ax in axes[len(chosen):]:
        ax.axis("off")

    plt.suptitle("Sample Annotated Images (training split)", fontsize=13, fontweight="bold")
    plt.tight_layout()
    out = RESULTS_DIR / "sample_grid.png"
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"  📊 sample_grid.png → {out}")
    return out


def write_analysis_report(cfg: dict, class_ids: list, boxes: list, img_sizes: list) -> None:
    counter = collections.Counter(class_ids)
    names   = cfg["names"]
    total   = sum(counter.values())
    vals    = list(counter.values())
    ratio   = max(vals) / max(1, min(vals)) if vals else 0

    ws = [b[2] for b in boxes]
    hs = [b[3] for b in boxes]

    lines = [
        "# Dataset Analysis Report — NXP Cup India 2026",
        "",
        "## Overview",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total annotations | {total} |",
        f"| Unique classes | {len(counter)} |",
        f"| Imbalance ratio (max/min) | {ratio:.1f}x |",
        f"| Mean bbox width (norm) | {np.mean(ws):.4f} |",
        f"| Mean bbox height (norm) | {np.mean(hs):.4f} |",
        f"| Unique image sizes | {len(set(img_sizes))} |",
        "",
        "## Class Distribution",
        "| Class | Name | Count | % |",
        "|-------|------|-------|---|",
    ]
    for cid in sorted(counter):
        n = names[cid] if cid < len(names) else f"Unknown({cid})"
        c = counter[cid]
        lines.append(f"| {cid} | {n} | {c} | {c/max(1,total)*100:.1f}% |")

    imbalance_note = ""
    if ratio > 10:
        imbalance_note = "🔴 **Severe class imbalance** detected. Recommend weighted loss or oversampling."
    elif ratio > 3:
        imbalance_note = "🟡 **Moderate imbalance** — monitor per-class AP. May need class weights."
    else:
        imbalance_note = "🟢 **Balanced dataset** — standard training is appropriate."

    lines += [
        "",
        f"**Imbalance note:** {imbalance_note}",
        "",
        "## Generated Visualizations",
        "- `results/class_distribution.png`",
        "- `results/bbox_stats.png`",
        "- `results/sample_grid.png`",
        "",
        "*Generated by 02_dataset_analysis.py*",
    ]
    out = REPORTS_DIR / "dataset_analysis.md"
    out.write_text("\n".join(lines))
    print(f"  📄 dataset_analysis.md → {out}")


def main() -> None:
    print("\n" + "═"*60)
    print("  PHASE 3 — Dataset Analysis & Visualization")
    print("═"*60)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    cfg = load_yaml()
    print("\n  Gathering annotations...")
    class_ids, boxes, img_sizes, tags = gather_all_labels(cfg)
    print(f"  Found {len(class_ids)} annotations across {len(set(tags))} splits")

    plot_class_distribution(class_ids, cfg["names"])
    plot_bbox_stats(boxes)
    plot_sample_grid(cfg)
    write_analysis_report(cfg, class_ids, boxes, img_sizes)

    print("\n" + "═"*60)
    print("  Phase 3 complete. Proceeding to Phase 4...")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
