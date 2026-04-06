"""
BookMyGig — Anomaly Detection Evaluation
==========================================
Evaluates Isolation Forest using:
  - Contamination rate analysis
  - Score distribution (normal vs anomalous)
  - Flagged review inspection
  - Precision/Recall vs synthetic ground truth

Run:  python -m evaluation.evaluate_anomaly
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PROCESSED_DIR, SAVED_MODELS_DIR, EVAL_REPORT_DIR, BOOKINGS_CSV
from models.anomaly_model import AnomalyModel
from utils.logging_config import get_logger

log = get_logger("eval_anomaly", "eval_anomaly.log")


def create_synthetic_ground_truth(df: pd.DataFrame) -> pd.Series:
    """
    Label reviews as anomalous (1) if:
      - text sentiment is very high (>0.7) but rating <= 2, OR
      - text sentiment is very low (<0.3) but rating >= 4
    """
    if "Sentiment_Score" not in df.columns:
        df["Sentiment_Score"] = (df["Rating"] - 1) / 4
    sent = df["Sentiment_Score"].fillna(0.5)
    rat  = df["Rating"].fillna(3)
    fake = ((sent > 0.7) & (rat <= 2)) | ((sent < 0.3) & (rat >= 4))
    return fake.astype(int)


def evaluate() -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Anomaly Detection Evaluation")
    log.info("=" * 60)

    scored_path = PROCESSED_DIR / "reviews_anomaly_scored.csv"
    if not scored_path.exists():
        log.warning("Anomaly-scored file not found — running training first")
        from training.train_anomaly import run
        run()

    df = pd.read_csv(scored_path)
    log.info(f"Loaded {len(df)} scored reviews")

    n_anomalies = df["is_anomaly"].sum()
    n_normal    = (~df["is_anomaly"]).sum()
    flagged_pct = n_anomalies / len(df) * 100

    # Score statistics
    anom_scores  = df.loc[df["is_anomaly"],  "anomaly_score"]
    normal_scores= df.loc[~df["is_anomaly"], "anomaly_score"]

    # Synthetic ground truth comparison
    gt = create_synthetic_ground_truth(df)
    from sklearn.metrics import precision_recall_fscore_support, roc_auc_score
    pred = df["is_anomaly"].astype(int)

    p, r, f, _ = precision_recall_fscore_support(gt, pred, average="binary", zero_division=0)
    try:
        auc = roc_auc_score(gt, -df["anomaly_score"])  # lower score = more anomalous
    except Exception:
        auc = 0.0

    metrics = {
        "total_reviews":      len(df),
        "flagged_anomalies":  int(n_anomalies),
        "normal_reviews":     int(n_normal),
        "flagged_pct":        round(flagged_pct, 2),
        "avg_anomaly_score":  round(df["anomaly_score"].mean(), 4),
        "anom_score_mean":    round(anom_scores.mean(), 4) if len(anom_scores) else 0,
        "normal_score_mean":  round(normal_scores.mean(), 4) if len(normal_scores) else 0,
        "vs_synthetic_gt": {
            "precision": round(p, 4),
            "recall":    round(r, 4),
            "f1":        round(f, 4),
            "roc_auc":   round(auc, 4),
        },
    }

    print("\n" + "=" * 60)
    print("  ANOMALY DETECTION EVALUATION RESULTS")
    print("=" * 60)
    print(f"  Total reviews     : {len(df):,}")
    print(f"  Flagged anomalies : {n_anomalies} ({flagged_pct:.1f}%)")
    print(f"  Normal reviews    : {n_normal}")
    print(f"  Avg anomaly score : {df['anomaly_score'].mean():.4f}")
    print(f"  Score (anomalous) : {anom_scores.mean():.4f}" if len(anom_scores) else "")
    print(f"  Score (normal)    : {normal_scores.mean():.4f}" if len(normal_scores) else "")
    print(f"\n  vs Synthetic Ground Truth:")
    print(f"    Precision : {p:.4f}")
    print(f"    Recall    : {r:.4f}")
    print(f"    F1        : {f:.4f}")
    print(f"    ROC-AUC   : {auc:.4f}")
    print("=" * 60 + "\n")

    report_path = EVAL_REPORT_DIR / "anomaly_evaluation.json"
    with open(report_path, "w") as fp:
        json.dump(metrics, fp, indent=2)
    log.info(f"Report saved → {report_path}")

    return metrics


if __name__ == "__main__":
    evaluate()
