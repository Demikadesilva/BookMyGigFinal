"""
BookMyGig — Master Training Orchestrator
=========================================
Runs the complete ML pipeline end-to-end:
  1. Data Cleaning
  2. Data Validation
  3. Sentiment Analysis Training
  4. Anomaly Detection Training
  5. Recommendation System Training
  6. Dynamic Pricing Training
  7. Demand Forecasting Training
  8. Evaluation Report

Run:  python -m training.train_all
      python training/train_all.py
      python training/train_all.py --skip-cleaning
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import EVAL_REPORT_DIR
from utils.logging_config import get_logger

log = get_logger("train_all", "train_all.log")


def _step(name: str, fn, skip: bool = False) -> dict:
    if skip:
        log.info(f"[SKIP] {name}")
        return {"skipped": True}
    log.info(f"\n{'='*60}")
    log.info(f"STEP: {name}")
    log.info(f"{'='*60}")
    t0 = time.time()
    try:
        result = fn()
        elapsed = time.time() - t0
        log.info(f"[OK] {name} completed in {elapsed:.1f}s")
        return result or {"status": "ok", "elapsed_s": round(elapsed, 1)}
    except Exception as e:
        log.error(f"[FAIL] {name}: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="BookMyGig Full Training Pipeline")
    parser.add_argument("--skip-cleaning",    action="store_true", help="Skip data cleaning step")
    parser.add_argument("--skip-validation",  action="store_true", help="Skip data validation step")
    parser.add_argument("--skip-sentiment",   action="store_true")
    parser.add_argument("--skip-anomaly",     action="store_true")
    parser.add_argument("--skip-recommender", action="store_true")
    parser.add_argument("--skip-pricing",     action="store_true")
    parser.add_argument("--skip-demand",      action="store_true")
    args = parser.parse_args()

    overall_start = time.time()
    results = {}

    print("\n" + "=" * 70)
    print("  BookMyGig AI — Complete Training Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")

    # 1. Data Cleaning
    from pipelines.data_cleaner import run_cleaning_pipeline
    results["cleaning"] = _step("Data Cleaning", run_cleaning_pipeline, skip=args.skip_cleaning)

    # 2. Data Validation
    from pipelines.data_validator import run_validation_pipeline
    results["validation"] = _step("Data Validation", run_validation_pipeline, skip=args.skip_validation)

    # 3. Sentiment Analysis
    from training.train_sentiment import run as train_sentiment
    results["sentiment"] = _step("Sentiment Analysis", train_sentiment, skip=args.skip_sentiment)

    # 4. Anomaly Detection
    from training.train_anomaly import run as train_anomaly
    results["anomaly"] = _step("Anomaly Detection", train_anomaly, skip=args.skip_anomaly)

    # 5. Recommendation System
    from training.train_recommendation import run as train_rec
    results["recommendation"] = _step("Recommendation System", train_rec, skip=args.skip_recommender)

    # 6. Dynamic Pricing
    from training.train_pricing import run as train_pricing
    results["pricing"] = _step("Dynamic Pricing", train_pricing, skip=args.skip_pricing)

    # 7. Demand Forecasting
    from training.train_demand import run as train_demand
    results["demand"] = _step("Demand Forecasting", train_demand, skip=args.skip_demand)

    total_time = time.time() - overall_start

    # Save training summary
    summary = {
        "completed_at": datetime.now().isoformat(),
        "total_time_s": round(total_time, 1),
        "results": results,
    }
    summary_path = EVAL_REPORT_DIR / "training_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=str)

    print("\n" + "=" * 70)
    print("  TRAINING PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Total time   : {total_time:.1f}s")
    print(f"  Summary saved: {summary_path}")
    print("\n  Step results:")
    for step, res in results.items():
        status = "SKIP" if res.get("skipped") else ("FAIL" if res.get("error") else "OK")
        print(f"    [{status:4s}] {step}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
