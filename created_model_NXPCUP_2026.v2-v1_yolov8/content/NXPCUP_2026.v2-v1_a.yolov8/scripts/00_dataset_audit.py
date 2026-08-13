"""
scripts/00_dataset_audit.py
============================
PHASE 1 — Dataset Integrity Audit (READ-ONLY)

Checks:
  - data.yaml validity
  - image / label counts per split
  - missing label / missing image detection
  - corrupted image detection (PIL)
  - empty label files (background images)
  - invalid YOLO annotation format
  - class ID range validation
  - bounding box sanity (values in [0,1])
  - class distribution & imbalance report

Outputs:
  - reports/dataset_report.md
  - Console summary
"""

from __future__ import annotations

import os
import sys
import yaml
import json
import collections
from pathlib import Path
from PIL import Image
from tqdm import tqdm

# ── Project root = parent of this script's parent ────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATASET_ROOT = PROJECT_ROOT
DATA_YAML    = PROJECT_ROOT / "data.yaml"
REPORTS_DIR  = PROJECT_ROOT / "reports"
SUPPORTED    = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def sep(title: str = "", w: int = 70) -> None:
    if title:
        pad = (w - len(title) - 2) // 2
        print(f"\n{'─'*pad} {title} {'─'*pad}")
    else:
        print("─" * w)


def ok(msg: str)   -> None: print(f"  ✅  {msg}")
def warn(msg: str) -> None: print(f"  ⚠️   {msg}")
def err(msg: str)  -> None: print(f"  ❌  {msg}")


# ─── YAML ────────────────────────────────────────────────────────────────────

def load_yaml() -> tuple[dict, dict[str, Path]]:
    sep("data.yaml")
    if not DATA_YAML.exists():
        err(f"data.yaml not found: {DATA_YAML}")
        sys.exit(1)

    with open(DATA_YAML) as f:
        cfg = yaml.safe_load(f)

    for k, v in cfg.items():
        print(f"    {k}: {v}")

    required = {"train", "val", "test", "nc", "names"}
    missing  = required - set(cfg.keys())
    if missing:
        err(f"Missing keys: {missing}")
    else:
        ok("All required keys present")

    nc, names = cfg["nc"], cfg["names"]
    if len(names) != nc:
        err(f"nc={nc} but {len(names)} names given — MISMATCH")
    else:
        ok(f"nc={nc} matches names: {names}")

    def resolve(raw: str, key: str) -> Path:
        p = Path(raw)
        if p.is_absolute() and p.exists():
            return p
        cand1 = (DATA_YAML.parent / p).resolve()
        if cand1.exists():
            return cand1
        # Handle cases where data.yaml has relative ../ leading paths
        clean_raw = raw.lstrip('./').lstrip('../')
        cand2 = (DATA_YAML.parent / clean_raw).resolve()
        if cand2.exists():
            return cand2
        alias = "valid" if key == "val" else key
        cand3 = (DATA_YAML.parent / alias / "images").resolve()
        if cand3.exists():
            return cand3
        return cand1

    splits = {
        "train": resolve(cfg["train"], "train"),
        "valid": resolve(cfg["val"], "val"),
        "test":  resolve(cfg["test"], "test"),
    }
    for name, p in splits.items():
        (ok if p.exists() else err)(f"{name} → {p}")

    return cfg, splits


# ─── COUNTS ──────────────────────────────────────────────────────────────────

def gather_split(name: str, img_dir: Path) -> dict:
    lbl_dir = img_dir.parent / "labels"
    images  = sorted(f for f in img_dir.iterdir() if f.suffix.lower() in SUPPORTED) \
              if img_dir.exists() else []
    labels  = sorted(f for f in lbl_dir.iterdir() if f.suffix.lower() == ".txt") \
              if lbl_dir.exists() else []
    return dict(name=name, img_dir=img_dir, lbl_dir=lbl_dir,
                images=images, labels=labels)


def report_counts(splits: dict) -> None:
    sep("File Counts")
    total_i = total_l = 0
    for d in splits.values():
        ni, nl = len(d["images"]), len(d["labels"])
        total_i += ni; total_l += nl
        flag = "✅" if ni > 0 else "❌"
        print(f"\n  [{d['name'].upper()}]")
        print(f"    {flag} Images : {ni:>5}  →  {d['img_dir']}")
        print(f"    {flag} Labels : {nl:>5}  →  {d['lbl_dir']}")
    print(f"\n  Total images : {total_i} | Total labels : {total_l}")
    (ok if total_i == 2167 else warn)(f"README claims 2167 — found {total_i}")


# ─── PAIRING ─────────────────────────────────────────────────────────────────

def check_pairing(splits: dict) -> dict[str, list]:
    sep("Label ↔ Image Pairing")
    issues: dict[str, list] = {}
    for d in splits.values():
        img_s = {f.stem for f in d["images"]}
        lbl_s = {f.stem for f in d["labels"]}
        miss_l = sorted(img_s - lbl_s)
        miss_i = sorted(lbl_s - img_s)
        issues[d["name"]] = dict(missing_labels=miss_l, missing_images=miss_i)
        print(f"\n  [{d['name'].upper()}]")
        (warn if miss_l else ok)(f"  {len(miss_l)} image(s) without label")
        (warn if miss_i else ok)(f"  {len(miss_i)} label(s) without image")
        for s in miss_l[:5]: print(f"      · {s}")
        for s in miss_i[:5]: print(f"      · {s}")
    return issues


# ─── CORRUPTION ──────────────────────────────────────────────────────────────

def check_corruption(splits: dict) -> dict[str, list]:
    sep("Corrupted Image Check")
    bad: dict[str, list] = {}
    for d in splits.values():
        corrupted = []
        for img in tqdm(d["images"], desc=f"  {d['name']}", unit="img", leave=False):
            try:
                with Image.open(img) as im:
                    im.verify()
            except Exception as e:
                corrupted.append((img.name, str(e)))
        bad[d["name"]] = corrupted
        (err if corrupted else ok)(f"  [{d['name'].upper()}] {len(corrupted)} corrupted")
        for n, r in corrupted[:5]:
            print(f"      · {n} — {r}")
    return bad


# ─── ANNOTATIONS ─────────────────────────────────────────────────────────────

def check_annotations(splits: dict, nc: int) -> tuple[dict, collections.Counter]:
    sep("Annotation Validation")
    counter: collections.Counter = collections.Counter()
    issues: dict = {}

    for d in splits.values():
        empty, bad_fmt, bad_cls, bad_box = [], [], [], []
        for lbl in tqdm(d["labels"], desc=f"  {d['name']}", unit="lbl", leave=False):
            lines = [l.strip() for l in lbl.read_text().splitlines() if l.strip()]
            if not lines:
                empty.append(lbl.name); continue
            for i, line in enumerate(lines):
                parts = line.split()
                if len(parts) != 5:
                    bad_fmt.append(f"{lbl.name}:L{i+1}"); continue
                try:
                    cid = int(parts[0]); cx, cy, w, h = map(float, parts[1:])
                except ValueError:
                    bad_fmt.append(f"{lbl.name}:L{i+1}"); continue
                counter[cid] += 1
                if not (0 <= cid < nc):
                    bad_cls.append(f"{lbl.name}:L{i+1} cid={cid}")
                if not (0 <= cx <= 1 and 0 <= cy <= 1 and 0 < w <= 1 and 0 < h <= 1):
                    bad_box.append(f"{lbl.name}:L{i+1} cx={cx:.3f} cy={cy:.3f} w={w:.3f} h={h:.3f}")

        issues[d["name"]] = dict(empty=empty, bad_fmt=bad_fmt, bad_cls=bad_cls, bad_box=bad_box)
        print(f"\n  [{d['name'].upper()}]")
        (warn if empty   else ok)(f"  {len(empty)} empty label files (background images)")
        (err  if bad_fmt else ok)(f"  {len(bad_fmt)} format errors")
        (err  if bad_cls else ok)(f"  {len(bad_cls)} class-ID out-of-range errors")
        (err  if bad_box else ok)(f"  {len(bad_box)} bounding-box sanity errors")

    return issues, counter


# ─── CLASS DISTRIBUTION ───────────────────────────────────────────────────────

def report_distribution(counter: collections.Counter, names: list[str]) -> None:
    sep("Class Distribution")
    total = sum(counter.values())
    print(f"\n  {'ID':<5} {'Class':<12} {'Count':>8}  {'%':>7}")
    print(f"  {'─'*5} {'─'*12} {'─'*8}  {'─'*7}")
    for cid in sorted(counter):
        name = names[cid] if cid < len(names) else f"Unknown({cid})"
        cnt  = counter[cid]
        print(f"  {cid:<5} {name:<12} {cnt:>8}  {cnt/total*100:>6.1f}%")
    print(f"  {'─'*36}")
    print(f"  {'TOTAL':<18} {total:>8}")
    vals = list(counter.values())
    if vals:
        ratio = max(vals) / max(1, min(vals))
        (ok   if ratio <= 3  else
         warn if ratio <= 10 else err)(f"  Imbalance ratio: {ratio:.1f}x")


# ─── MARKDOWN REPORT ─────────────────────────────────────────────────────────

def write_report(cfg: dict, splits: dict, pairing: dict,
                 corruption: dict, ann_issues: dict,
                 counter: collections.Counter) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    names = cfg["names"]
    total_i = sum(len(d["images"]) for d in splits.values())
    total_l = sum(len(d["labels"]) for d in splits.values())
    total_ann = sum(counter.values())
    vals = list(counter.values())
    ratio = max(vals) / max(1, min(vals)) if vals else 0

    lines = [
        "# Dataset Report — NXP Cup India 2026",
        "",
        "## Summary",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total images | {total_i} |",
        f"| Total labels | {total_l} |",
        f"| Total annotations | {total_ann} |",
        f"| Classes (nc) | {cfg['nc']} |",
        f"| Class names | {', '.join(names)} |",
        f"| Image size (README) | 512×512 |",
        f"| Imbalance ratio | {ratio:.1f}x |",
        "",
        "## Split Distribution",
        "| Split | Images | Labels |",
        "|-------|--------|--------|",
    ]
    for d in splits.values():
        lines.append(f"| {d['name']} | {len(d['images'])} | {len(d['labels'])} |")

    lines += [
        "",
        "## Class Distribution",
        "| Class ID | Name | Count | % |",
        "|----------|------|-------|---|",
    ]
    total = sum(counter.values())
    for cid in sorted(counter):
        n  = names[cid] if cid < len(names) else f"Unknown({cid})"
        c  = counter[cid]
        lines.append(f"| {cid} | {n} | {c} | {c/max(1,total)*100:.1f}% |")

    lines += [
        "",
        "## Data Quality Issues",
    ]
    any_issue = False
    for split, pi in pairing.items():
        ml = pi["missing_labels"]; mi = pi["missing_images"]
        ci = corruption.get(split, [])
        ai = ann_issues.get(split, {})
        if ml or mi or ci or any(ai.values()):
            any_issue = True
            lines.append(f"\n### {split}")
            if ml:  lines.append(f"- Missing labels: {len(ml)}")
            if mi:  lines.append(f"- Missing images: {len(mi)}")
            if ci:  lines.append(f"- Corrupted images: {len(ci)}")
            for k in ["empty", "bad_fmt", "bad_cls", "bad_box"]:
                v = ai.get(k, [])
                if v: lines.append(f"- {k}: {len(v)}")
    if not any_issue:
        lines.append("\n✅ No issues found — dataset is clean.")

    lines += [
        "",
        "## Audit Verdict",
        "✅ **PASSED** — Dataset ready for training." if not any_issue
        else "⚠️ **WARNINGS** — Review issues before training.",
        "",
        "*Generated by 00_dataset_audit.py*",
    ]

    out = REPORTS_DIR / "dataset_report.md"
    out.write_text("\n".join(lines))
    print(f"\n  📄 Report saved → {out}")


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n" + "═"*70)
    print("  NXP CUP INDIA 2026  ·  PHASE 1 — Dataset Integrity Audit")
    print("  READ-ONLY — Dataset will NOT be modified.")
    print("═"*70)

    cfg, split_paths = load_yaml()
    nc, names = cfg["nc"], cfg["names"]

    splits = {k: gather_split(k, v) for k, v in split_paths.items()}

    report_counts(splits)
    pairing    = check_pairing(splits)
    corruption = check_corruption(splits)
    ann_issues, counter = check_annotations(splits, nc)
    report_distribution(counter, names)
    write_report(cfg, splits, pairing, corruption, ann_issues, counter)

    sep("AUDIT COMPLETE")
    print("\n  See reports/dataset_report.md for the full report.")
    print("  Proceeding to Phase 2 automatically...\n")
    print("═"*70 + "\n")


if __name__ == "__main__":
    main()
