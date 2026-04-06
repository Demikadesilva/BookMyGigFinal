"""
BookMyGig — Anomaly Detection Training Script
==============================================
Trains Isolation Forest on review data to detect fake/suspicious reviews.
Saves: saved_models/anomaly/

Run:  python -m training.train_anomaly
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    REVIEWS_CSV, BOOKINGS_CSV, PROCESSED_DIR, SAVED_MODELS_DIR,
    ISOLATION_FOREST_CONTAMINATION, ISOLATION_FOREST_ESTIMATORS, RANDOM_SEED,
)
from models.anomaly_model import AnomalyModel, FEATURE_COLS
from utils.logging_config import get_logger

log = get_logger("train_anomaly", "train_anomaly.log")


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    # Reviews
    rev_clean = PROCESSED_DIR / "reviews_with_sentiment.csv"
    rev_path  = rev_clean if rev_clean.exists() else REVIEWS_CSV
    reviews   = pd.read_csv(rev_path)

    # Bookings
    bk_clean = PROCESSED_DIR / "bookings_clean.csv"
    bk_path  = bk_clean if bk_clean.exists() else BOOKINGS_CSV
    bookings  = pd.read_csv(bk_path)
    return reviews, bookings


def run() -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Anomaly Detection Training")
    log.info("=" * 60)

    reviews, bookings = load_data()
    log.info(f"Reviews: {len(reviews):,} | Bookings: {len(bookings):,}")

    # Join musician avg rating
    musician_avg = bookings.groupby("Musician_ID")["Rating"].mean().rename("Avg_Musician_Rating").reset_index()
    if "Musician_ID" not in reviews.columns:
        reviews = reviews.merge(
            bookings[["Booking_ID", "Musician_ID"]], on="Booking_ID", how="left"
        )
    reviews = reviews.merge(musician_avg, on="Musician_ID", how="left")
    reviews["Avg_Musician_Rating"] = reviews["Avg_Musician_Rating"].fillna(reviews["Rating"].mean())

    # Add Sentiment_Score if missing
    if "Sentiment_Score" not in reviews.columns:
        reviews["Sentiment_Score"] = (pd.to_numeric(reviews["Rating"], errors="coerce") - 1) / 4

    # Train model
    model = AnomalyModel(
        contamination=ISOLATION_FOREST_CONTAMINATION,
        n_estimators=ISOLATION_FOREST_ESTIMATORS,
        random_state=RANDOM_SEED,
    )
    model.fit(reviews)
    metrics = model.evaluate(reviews)
    log.info(f"Flagged anomalies: {metrics['flagged_anomalies']} / {metrics['total_reviews']} ({metrics['flagged_pct']:.1f}%)")

    # Save predictions to processed/
    result_df = model.predict(reviews)
    out_path = PROCESSED_DIR / "reviews_anomaly_scored.csv"
    result_df.to_csv(out_path, index=False)
    log.info(f"Anomaly-scored reviews saved → {out_path}")

    # Save model
    save_path = SAVED_MODELS_DIR / "anomaly"
    model.save(save_path)
    log.info(f"Anomaly model saved → {save_path}")

    # Inspect top anomalies
    anomalies = result_df[result_df["is_anomaly"]].sort_values("anomaly_score").head(5)
    log.info("Top suspicious reviews:")
    for _, row in anomalies.iterrows():
        text_snippet = str(row.get("Review_Text", ""))[:60]
        log.info(f"  [{row.get('Review_ID','?')}] Rating={row['Rating']} Sent={row.get('Sentiment_Score',0):.2f} | {text_snippet}...")

    print("\n" + "=" * 55)
    print("  ANOMALY DETECTION TRAINING COMPLETE")
    print("=" * 55)
    print(f"  Total reviews      : {metrics['total_reviews']:,}")
    print(f"  Anomalies flagged  : {metrics['flagged_anomalies']} ({metrics['flagged_pct']:.1f}%)")
    print(f"  Avg anomaly score  : {metrics['avg_anomaly_score']:.4f}")
    print("=" * 55 + "\n")

    return metrics


if __name__ == "__main__":
    run()
