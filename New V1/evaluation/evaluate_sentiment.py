"""
BookMyGig — Sentiment Evaluation
==================================
Evaluates the sentiment model using held-out test data.
Metrics: Accuracy, Precision, Recall, F1, Confusion Matrix, ROC-AUC

Run:  python -m evaluation.evaluate_sentiment
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import (
    classification_report, confusion_matrix, accuracy_score,
    precision_recall_fscore_support, roc_auc_score
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import label_binarize

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import PROCESSED_DIR, SAVED_MODELS_DIR, EVAL_REPORT_DIR, RANDOM_SEED
from models.sentiment_model import SentimentModel
from utils.logging_config import get_logger

log = get_logger("eval_sentiment", "eval_sentiment.log")


def rating_to_label(r: int) -> str:
    if r >= 4: return "POSITIVE"
    elif r == 3: return "NEUTRAL"
    else: return "NEGATIVE"

def score_to_label(score: float) -> str:
    """Uses the same thresholds defined in sentiment_model.py"""
    if pd.isna(score): return "NEUTRAL"
    if score >= 0.6: return "POSITIVE"
    elif score <= 0.4: return "NEGATIVE"
    else: return "NEUTRAL"

def get_metrics(y_true, y_pred, labels):
    """Helper function to calculate all metrics for a given prediction set."""
    acc = accuracy_score(y_true, y_pred)
    p, r, f, _ = precision_recall_fscore_support(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    
    y_true_bin = label_binarize(y_true, classes=labels)
    y_pred_bin = label_binarize(y_pred, classes=labels)
    auc = roc_auc_score(y_true_bin, y_pred_bin, average="macro", multi_class="ovr")
    
    return {
        "accuracy": round(acc, 4),
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1_score": round(f, 4),
        "roc_auc": round(auc, 4)
    }

def evaluate() -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Sentiment Evaluation (VADER vs BERT)")
    log.info("=" * 60)

    # Load annotated reviews
    path = PROCESSED_DIR / "reviews_with_sentiment.csv"
    if not path.exists():
        log.warning("reviews_with_sentiment.csv not found — running training first")
        from training.train_sentiment import run
        run()

    df = pd.read_csv(path)
    df["true_label"] = df["Rating"].apply(rating_to_label)
    
    # Generate labels for individual models based on their raw scores in the CSV
    df["vader_label"] = df.get("vader_score", df["Sentiment_Score"]).apply(score_to_label)
    df["bert_label"] = df.get("bert_score", df["Sentiment_Score"]).apply(score_to_label)
    df["blended_label"] = df.get("Sentiment_Label", df.get("sentiment_label", "POSITIVE"))

    _, test_df = train_test_split(df, test_size=0.2, random_state=RANDOM_SEED, stratify=df["true_label"])

    y_true = test_df["true_label"]
    labels = ["POSITIVE", "NEUTRAL", "NEGATIVE"]

    # Calculate metrics for all three approaches
    vader_metrics = get_metrics(y_true, test_df["vader_label"], labels)
    bert_metrics = get_metrics(y_true, test_df["bert_label"], labels)
    blended_metrics = get_metrics(y_true, test_df["blended_label"], labels)

    metrics = {
        "test_size": len(test_df),
        "models": {
            "VADER": vader_metrics,
            "DistilBERT": bert_metrics,
            "Blended": blended_metrics
        }
    }

    # ── Print ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("  SENTIMENT MODEL EVALUATION RESULTS (SIDE-BY-SIDE)")
    print("=" * 70)
    print(f"  Test set size : {len(test_df)}")
    print(f"  {'Model':<15} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8} | {'ROC-AUC'}")
    print("-" * 70)
    
    for name, m in metrics["models"].items():
        print(f"  {name:<15} | {m['accuracy']:<8.4f} | {m['precision']:<9.4f} | {m['recall']:<8.4f} | {m['f1_score']:<8.4f} | {m['roc_auc']:.4f}")
    
    print("=" * 70 + "\n")

    # Save report
    report_path = EVAL_REPORT_DIR / "sentiment_evaluation.json"
    with open(report_path, "w") as f_:
        json.dump(metrics, f_, indent=2, default=str)
    log.info(f"Report saved → {report_path}")

    return metrics


if __name__ == "__main__":
    evaluate()