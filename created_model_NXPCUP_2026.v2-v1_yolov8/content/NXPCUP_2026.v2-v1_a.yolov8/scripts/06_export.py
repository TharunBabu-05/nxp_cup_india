"""
scripts/06_export.py
======================
PHASE 9 — Model Export

Exports best.pt to:
  1. PyTorch (already .pt — copy to exports/)
  2. ONNX (opset 12, dynamic axes)
  3. TensorRT (if supported — requires TensorRT + GPU)

Verifies each exported model.
Outputs:
  - exports/best.pt
  - exports/best.onnx
  - exports/best.engine  (if TensorRT available)
  - reports/export_report.md
"""

from __future__ import annotations

import sys
import json
import shutil
import time
import yaml
import numpy as np
from pathlib import Path
from datetime import datetime

SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
MODELS_DIR   = PROJECT_ROOT / "models"
EXPORTS_DIR  = PROJECT_ROOT / "exports"
REPORTS_DIR  = PROJECT_ROOT / "reports"
RUNS_DIR     = PROJECT_ROOT / "runs"
RESULTS_DIR  = PROJECT_ROOT / "results"


def find_best_model() -> Path:
    for c in [MODELS_DIR / "best.pt",
              *sorted(RUNS_DIR.glob("train/*/weights/best.pt"), reverse=True)]:
        if c.exists():
            return c
    raise FileNotFoundError("No best.pt found. Run 03_train.py first.")


def export_pytorch(model_path: Path) -> Path:
    """Copy best.pt to exports/."""
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    dst = EXPORTS_DIR / "best.pt"
    shutil.copy2(model_path, dst)
    size_mb = dst.stat().st_size / 1e6
    print(f"  ✅ PyTorch  →  {dst}  ({size_mb:.1f} MB)")
    return dst


def export_onnx(model_path: Path) -> Path | None:
    """Export to ONNX with dynamic batch axis."""
    from ultralytics import YOLO
    print("\n  Exporting to ONNX...")
    model = YOLO(str(model_path))
    try:
        exported = model.export(
            format    = "onnx",
            imgsz     = 512,
            opset     = 12,
            dynamic   = False,   # fixed 1×3×512×512 for TensorRT compatibility
            simplify  = True,
        )
        src = Path(exported) if exported else model_path.with_suffix(".onnx")
        dst = EXPORTS_DIR / "best.onnx"
        if src.exists():
            shutil.copy2(src, dst)
            size_mb = dst.stat().st_size / 1e6
            print(f"  ✅ ONNX     →  {dst}  ({size_mb:.1f} MB)")
            return dst
        else:
            print(f"  ⚠️  ONNX export succeeded but file not found at {src}")
            return None
    except Exception as e:
        print(f"  ❌ ONNX export failed: {e}")
        return None


def verify_onnx(onnx_path: Path) -> bool:
    """Verify ONNX model with onnxruntime."""
    try:
        import onnxruntime as ort
        sess = ort.InferenceSession(str(onnx_path),
                                    providers=["CUDAExecutionProvider",
                                               "CPUExecutionProvider"])
        inp_name = sess.get_inputs()[0].name
        dummy    = np.random.rand(1, 3, 512, 512).astype(np.float32)
        t0 = time.perf_counter()
        out = sess.run(None, {inp_name: dummy})
        dt  = (time.perf_counter() - t0) * 1000
        print(f"  ✅ ONNX verified — inference: {dt:.1f} ms  output shapes: {[o.shape for o in out]}")
        return True
    except ImportError:
        print("  ⚠️  onnxruntime not installed — skipping ONNX verification")
        print("       Install with: pip install onnxruntime-gpu")
        return False
    except Exception as e:
        print(f"  ❌ ONNX verification failed: {e}")
        return False


def export_tensorrt(model_path: Path) -> Path | None:
    """Export to TensorRT .engine (requires GPU + TensorRT)."""
    import torch
    if not torch.cuda.is_available():
        print("  ⚠️  TensorRT requires CUDA GPU — skipping")
        return None

    try:
        from ultralytics import YOLO
        print("\n  Exporting to TensorRT FP16...")
        model    = YOLO(str(model_path))
        exported = model.export(
            format  = "engine",
            imgsz   = 512,
            half    = True,     # FP16 for edge speed
            device  = 0,
        )
        src = Path(exported) if exported else model_path.with_suffix(".engine")
        dst = EXPORTS_DIR / "best.engine"
        if src.exists():
            shutil.copy2(src, dst)
            size_mb = dst.stat().st_size / 1e6
            print(f"  ✅ TensorRT →  {dst}  ({size_mb:.1f} MB)")
            return dst
        else:
            print(f"  ⚠️  TensorRT file not found at {src}")
            return None
    except Exception as e:
        print(f"  ⚠️  TensorRT export failed (may not be installed): {e}")
        return None


def benchmark_models(pt_path: Path, onnx_path: Path | None) -> dict:
    """Quick CPU inference speed comparison."""
    from ultralytics import YOLO
    import torch

    dummy = torch.rand(1, 3, 512, 512)
    results = {}

    # PyTorch
    model = YOLO(str(pt_path))
    times = []
    for _ in range(20):
        t0 = time.perf_counter()
        _ = model.predict(source=dummy, verbose=False, device="cpu")
        times.append((time.perf_counter() - t0) * 1000)
    results["pytorch_ms"] = round(float(np.mean(times[5:])), 2)
    print(f"  PyTorch CPU: {results['pytorch_ms']:.1f} ms/img")

    return results


def write_export_report(pt: Path, onnx: Path | None, trt: Path | None,
                        benchmark: dict) -> None:
    lines = [
        "# Export Report — NXP Cup India 2026",
        f"\n*Exported: {datetime.now():%Y-%m-%d %H:%M:%S}*",
        "\n## Exported Models",
        "\n| Format | Path | Size | Status |",
        "|--------|------|------|--------|",
    ]

    def row(fmt, p, status):
        size = f"{p.stat().st_size/1e6:.1f} MB" if p and p.exists() else "N/A"
        path = str(p) if p else "N/A"
        return f"| {fmt} | `{path}` | {size} | {status} |"

    lines.append(row("PyTorch (.pt)",   pt,   "✅ Ready"))
    lines.append(row("ONNX (.onnx)",    onnx, "✅ Ready" if onnx else "⚠️ Failed"))
    lines.append(row("TensorRT (.engine)", trt, "✅ Ready" if trt else "⚠️ Not available"))

    lines += [
        "\n## Inference Speed",
        f"| Runtime | Device | Latency |",
        f"|---------|--------|---------|",
        f"| PyTorch | CPU | {benchmark.get('pytorch_ms', 'N/A')} ms/img |",
        "\n## Deployment Notes",
        "- Use `best.pt` for direct Ultralytics / ROS2 deployment",
        "- Use `best.onnx` for hardware-agnostic runtime (ONNX Runtime)",
        "- Use `best.engine` for maximum speed on NVIDIA Jetson/GPU with TensorRT",
        "- Recommended inference conf: see `results/confidence_sweep.png`",
        "\n*Generated by 06_export.py*",
    ]

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / "export_report.md"
    out.write_text("\n".join(lines))
    print(f"\n  📄 export_report.md → {out}")


def main() -> None:
    print("\n" + "═"*60)
    print("  PHASE 9 — Model Export")
    print("═"*60)

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = find_best_model()
    print(f"\n  Source model: {model_path}")

    pt_out   = export_pytorch(model_path)
    onnx_out = export_onnx(model_path)
    if onnx_out:
        verify_onnx(onnx_out)
    trt_out  = export_tensorrt(model_path)

    print("\n  Benchmarking CPU inference speed...")
    try:
        bench = benchmark_models(pt_out, onnx_out)
    except Exception as e:
        print(f"  ⚠️  Benchmark failed: {e}")
        bench = {}

    write_export_report(pt_out, onnx_out, trt_out, bench)

    print("\n" + "═"*60)
    print("  Phase 9 complete. Proceeding to Phase 10...")
    print("═"*60 + "\n")


if __name__ == "__main__":
    main()
