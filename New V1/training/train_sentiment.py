"""
BookMyGig — Sentiment Analysis Training Script
================================================
Trains the VADER + DistilBERT ensemble on the reviews dataset.
Saves: saved_models/sentiment/

Run:  python -m training.train_sentiment
"""

import sys
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import REVIEWS_CSV, PROCESSED_DIR, SAVED_MODELS_DIR, RANDOM_SEED
from models.sentiment_model import SentimentModel
from utils.logging_config import get_logger

log = get_logger("train_sentiment", "train_sentiment.log")


def load_reviews() -> pd.DataFrame:
    clean_path = PROCESSED_DIR / "reviews_clean.csv"
    path = clean_path if clean_path.exists() else REVIEWS_CSV
    log.info(f"Loading reviews from {path}")
    df = pd.read_csv(path)
    df["Review_Text"] = df["Review_Text"].fillna("").astype(str)
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(3).clip(1, 5).astype(int)
    return df


def evaluate_sentiment(df: pd.DataFrame, results: pd.DataFrame) -> dict:
    """Compute accuracy-style metrics against ground-truth ratings."""
    # Convert rating to sentiment label
    def rating_to_label(r):
        if r >= 4:
            return "POSITIVE"
        elif r == 3:
            return "NEUTRAL"
        else:
            return "NEGATIVE"

    true_labels = df["Rating"].apply(rating_to_label)
    pred_labels = results["sentiment_label"]

    accuracy = (true_labels == pred_labels).mean()

    # Per-class metrics
    from sklearn.metrics import classification_report
    report = classification_report(
        true_labels, pred_labels,
        labels=["POSITIVE", "NEUTRAL", "NEGATIVE"],
        output_dict=True,
        zero_division=0
    )

    return {
        "accuracy": round(accuracy, 4),
        "classification_report": report,
        "avg_sentiment_score": round(results["sentiment_score"].mean(), 4),
        "sentiment_distribution": results["sentiment_label"].value_counts().to_dict(),
    }


def run() -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Sentiment Analysis Training")
    log.info("=" * 60)

    df = load_reviews()
    log.info(f"Reviews loaded: {len(df):,}")

    # Stage 1: VADER only (fast, no GPU required)
    log.info("Stage 1: Running VADER sentiment analysis...")
    t0 = time.time()
    model = SentimentModel(use_bert=False)
    vader_results = model.predict_series(df["Review_Text"])
    vader_time = time.time() - t0
    log.info(f"VADER completed in {vader_time:.1f}s")

    vader_metrics = evaluate_sentiment(df, vader_results)
    log.info(f"VADER Accuracy: {vader_metrics['accuracy']:.4f}")

    # Stage 2: BERT (if available)
    log.info("Stage 2: Running DistilBERT sentiment analysis...")
    try:
        t0 = time.time()
        full_model = SentimentModel(use_bert=True)
        # Run on sample if dataset is large
        sample_size = min(len(df), 500)
        sample_df = df.sample(sample_size, random_state=RANDOM_SEED)
        bert_results = full_model.predict_series(sample_df["Review_Text"])
        bert_time = time.time() - t0
        log.info(f"DistilBERT completed in {bert_time:.1f}s on {sample_size} samples")

        bert_metrics = evaluate_sentiment(sample_df.reset_index(drop=True), bert_results)
        log.info(f"BERT+VADER Ensemble Accuracy: {bert_metrics['accuracy']:.4f}")
        use_bert = True
    except Exception as e:
        log.warning(f"BERT unavailable ({e}) — using VADER only")
        full_model = model
        bert_metrics = vader_metrics
        use_bert = False

    # Annotate full reviews dataset with sentiment scores
    log.info("Annotating full dataset with sentiment scores...")
    annotated = full_model.predict_series(df["Review_Text"])  # VADER for all
    df_out = df.copy()
    df_out["vader_score"]     = annotated["vader_score"].values
    df_out["bert_score"]      = annotated["bert_score"].values
    df_out["Sentiment_Score"] = annotated["sentiment_score"].values
    df_out["Sentiment_Label"] = annotated["sentiment_label"].values

    # Save annotated reviews to processed/
    out_path = PROCESSED_DIR / "reviews_with_sentiment.csv"
    df_out.to_csv(out_path, index=False)
    log.info(f"Annotated reviews saved → {out_path}")

    # Save model
    save_path = SAVED_MODELS_DIR / "sentiment"
    full_model.save(save_path)
    log.info(f"Sentiment model saved → {save_path}")

    metrics = {
        "vader_metrics":  vader_metrics,
        "bert_metrics":   bert_metrics,
        "use_bert":       use_bert,
        "total_reviews":  len(df),
        "sentiment_dist": df_out["Sentiment_Label"].value_counts().to_dict(),
    }

    # Print summary
    print("\n" + "=" * 55)
    print("  SENTIMENT ANALYSIS TRAINING COMPLETE")
    print("=" * 55)
    print(f"  Reviews processed : {len(df):,}")
    print(f"  VADER Accuracy    : {vader_metrics['accuracy']:.4f}")
    print(f"  Ensemble Accuracy : {bert_metrics['accuracy']:.4f}")
    print(f"  Sentiment distribution:")
    for k, v in df_out["Sentiment_Label"].value_counts().items():
        print(f"    {k:10s} : {v:>4} ({v/len(df)*100:.1f}%)")
    print("=" * 55 + "\n")

    return metrics


if __name__ == "__main__":
    run()
