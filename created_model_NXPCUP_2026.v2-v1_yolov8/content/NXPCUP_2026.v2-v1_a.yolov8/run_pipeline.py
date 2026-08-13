"""
run_pipeline.py
================
MASTER PIPELINE ORCHESTRATOR — NXP Cup India 2026

Runs all phases in sequence, automatically continuing on success.
Stops only on unrecoverable errors.

Usage:
  python run_pipeline.py              # Run all phases
  python run_pipeline.py --start 3   # Resume from Phase 3
  python run_pipeline.py --only 1    # Run only Phase 1

Phases:
  1  Dataset Audit        (scripts/00_dataset_audit.py)
  2  Environment Setup    (scripts/01_env_setup.py)
  3  Dataset Analysis     (scripts/02_dataset_analysis.py)
  4  Training             (scripts/03_train.py)
  5  Evaluation           (scripts/04_evaluate.py)
  6  Error Analysis       (scripts/05_analyze_errors.py)
  7  Export               (scripts/06_export.py)
"""

from __future__ import annotations

import sys
import time
import argparse
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
LOG_FILE     = PROJECT_ROOT / "logs" / f"pipeline_{datetime.now():%Y%m%d_%H%M%S}.log"


PHASES = {
    1: ("Dataset Audit",        PROJECT_ROOT / "scripts" / "00_dataset_audit.py"),
    2: ("Environment Setup",    PROJECT_ROOT / "scripts" / "01_env_setup.py"),
    3: ("Dataset Analysis",     PROJECT_ROOT / "scripts" / "02_dataset_analysis.py"),
    4: ("Training",             PROJECT_ROOT / "scripts" / "03_train.py"),
    5: ("Evaluation",           PROJECT_ROOT / "scripts" / "04_evaluate.py"),
    6: ("Error Analysis",       PROJECT_ROOT / "scripts" / "05_analyze_errors.py"),
    7: ("Export",               PROJECT_ROOT / "scripts" / "06_export.py"),
}

# These phases can be skipped if artifacts exist
SKIPPABLE = {
    1: PROJECT_ROOT / "reports" / "dataset_report.md",
    2: PROJECT_ROOT / "reports" / "env_report.md",
    3: PROJECT_ROOT / "results" / "class_distribution.png",
    5: PROJECT_ROOT / "reports" / "evaluation.md",
    6: PROJECT_ROOT / "results" / "confidence_sweep.png",
    7: PROJECT_ROOT / "exports" / "best.onnx",
}


def banner(text: str) -> None:
    w = 70
    print("\n" + "█"*w)
    pad = (w - len(text) - 2) // 2
    print(f"█{' '*pad} {text} {' '*pad}█")
    print("█"*w + "\n")


def run_phase(phase_id: int, force: bool = False) -> bool:
    name, script = PHASES[phase_id]

    # Skip if artifact exists and not forced
    if not force and phase_id in SKIPPABLE:
        artifact = SKIPPABLE[phase_id]
        if artifact.exists():
            print(f"  ⏭️  Phase {phase_id} [{name}] — artifact exists, skipping.")
            print(f"      ({artifact})")
            return True

    banner(f"PHASE {phase_id}  ·  {name}")

    if not script.exists():
        print(f"  ❌ Script not found: {script}")
        return False

    t0  = time.perf_counter()
    ret = subprocess.run([sys.executable, str(script)], cwd=str(PROJECT_ROOT))
    dt  = time.perf_counter() - t0

    if ret.returncode == 0:
        print(f"\n  ✅ Phase {phase_id} [{name}] completed in {dt/60:.1f} min")
        return True
    else:
        print(f"\n  ❌ Phase {phase_id} [{name}] FAILED (exit code {ret.returncode})")
        print(f"     Check logs above. Fix the issue and re-run:")
        print(f"     python run_pipeline.py --start {phase_id}")
        return False


def main() -> None:
    p = argparse.ArgumentParser(description="NXP Cup India 2026 — Pipeline Orchestrator")
    p.add_argument("--start",  type=int, default=1,    help="Start from phase N")
    p.add_argument("--end",    type=int, default=7,    help="Stop after phase N")
    p.add_argument("--only",   type=int, default=None, help="Run only phase N")
    p.add_argument("--force",  action="store_true",    help="Re-run even if artifacts exist")
    args = p.parse_args()

    # Create log dir
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    banner("NXP CUP INDIA 2026 — AUTONOMOUS TRAINING PIPELINE")
    print(f"  Start time : {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"  Project    : {PROJECT_ROOT}")
    print(f"  Python     : {sys.executable}\n")

    if args.only is not None:
        phases_to_run = [args.only]
    else:
        phases_to_run = list(range(args.start, args.end + 1))

    print(f"  Phases to run: {phases_to_run}")

    start_time = time.perf_counter()
    results    = {}

    for phase_id in phases_to_run:
        if phase_id not in PHASES:
            print(f"  ⚠️  Phase {phase_id} does not exist. Skipping.")
            continue

        ok = run_phase(phase_id, force=args.force)
        results[phase_id] = ok

        if not ok:
            # Phase 4 (training) failure is unrecoverable — stop
            # Other phases can continue
            if phase_id == 4:
                print("\n  ⛔ Training failed — cannot proceed to evaluation.")
                print("     Fix the training error and resume with:")
                print(f"     python run_pipeline.py --start 4")
                break
            else:
                print(f"\n  ⚠️  Phase {phase_id} failed — continuing with next phase.")

    # Summary
    elapsed = time.perf_counter() - start_time
    banner("PIPELINE COMPLETE")
    print(f"  Total time : {elapsed/60:.1f} minutes")
    print(f"\n  {'Phase':<6} {'Name':<25} {'Status'}")
    print(f"  {'─'*6} {'─'*25} {'─'*10}")
    for pid, ok in results.items():
        name = PHASES[pid][0]
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"  {pid:<6} {name:<25} {status}")

    all_passed = all(results.values())
    print()
    if all_passed:
        print("  🎉 All phases completed successfully!")
        print("\n  Key artifacts:")
        artifacts = [
            ("Best model",         PROJECT_ROOT / "models" / "best.pt"),
            ("Last model",         PROJECT_ROOT / "models" / "last.pt"),
            ("ONNX model",         PROJECT_ROOT / "exports" / "best.onnx"),
            ("Dataset report",     PROJECT_ROOT / "reports" / "dataset_report.md"),
            ("Evaluation report",  PROJECT_ROOT / "reports" / "evaluation.md"),
            ("Confusion matrix",   PROJECT_ROOT / "results" / "confusion_matrix.png"),
            ("PR curve",           PROJECT_ROOT / "results" / "PR_curve.png"),
        ]
        for label, path in artifacts:
            exists = "✅" if path.exists() else "⚠️ "
            print(f"  {exists}  {label:<22}: {path}")
    else:
        print("  ⚠️  Some phases failed — review errors above.")
    print()


if __name__ == "__main__":
    main()
