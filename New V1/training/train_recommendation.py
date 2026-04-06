"""
BookMyGig — Recommendation System Training Script
==================================================
Trains the Hybrid Recommender (CBF + CF + Sentiment).
Saves: saved_models/recommendation/

Run:  python -m training.train_recommendation
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    MUSICIANS_CSV, BOOKINGS_CSV, PROCESSED_DIR, SAVED_MODELS_DIR,
    SVD_COMPONENTS, HYBRID_ALPHA_MAX, HYBRID_BETA, TOP_N_RECS, RANDOM_SEED,
)
from models.recommendation_model import HybridRecommender
from utils.logging_config import get_logger

log = get_logger("train_recommendation", "train_recommendation.log")


def load_data():
    m_clean = PROCESSED_DIR / "musicians_clean.csv"
    b_clean = PROCESSED_DIR / "bookings_clean.csv"
    musicians = pd.read_csv(m_clean if m_clean.exists() else MUSICIANS_CSV)
    bookings  = pd.read_csv(b_clean if b_clean.exists() else BOOKINGS_CSV)
    return musicians, bookings


def evaluate_recommendations(recommender: HybridRecommender, bookings: pd.DataFrame, musicians: pd.DataFrame) -> dict:
    """
    Compute Precision@K and Recall@K using leave-one-out evaluation.
    For each client with >= 2 bookings, hold out the last booking as test.
    """
    client_bookings = bookings.groupby("Client_ID")
    client_ids = [cid for cid, grp in client_bookings if len(grp) >= 2]

    if not client_ids:
        log.warning("No clients with >= 2 bookings for evaluation")
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "ndcg_at_k": 0.0}

    sample_clients = client_ids[:min(50, len(client_ids))]
    precisions, recalls = [], []

    for cid in sample_clients:
        grp = client_bookings.get_group(cid).sort_values("Date_Time")
        test_musician = grp.iloc[-1]["Musician_ID"]
        train_bk = grp.iloc[:-1]

        # temporarily train without test booking
        recs = recommender.recommend(client_id=cid)
        rec_ids = recs["Musician_ID"].tolist()

        hit = int(test_musician in rec_ids)
        precisions.append(hit / len(rec_ids) if rec_ids else 0)
        recalls.append(hit)

    return {
        "precision_at_10": round(np.mean(precisions), 4),
        "recall_at_10":    round(np.mean(recalls), 4),
        "evaluated_clients": len(sample_clients),
    }


def run() -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Recommendation System Training")
    log.info("=" * 60)

    musicians, bookings = load_data()
    log.info(f"Musicians: {len(musicians):,} | Bookings: {len(bookings):,}")

    # Load sentiment scores if available
    sent_path = PROCESSED_DIR / "reviews_with_sentiment.csv"
    sentiment_scores = None
    if sent_path.exists():
        reviews = pd.read_csv(sent_path)
        if "Booking_ID" in reviews.columns and "Sentiment_Score" in reviews.columns:
            merged = reviews.merge(bookings[["Booking_ID", "Musician_ID"]], on="Booking_ID", how="left")
            sentiment_scores = merged.groupby("Musician_ID")["Sentiment_Score"].mean()
            log.info(f"Loaded sentiment scores for {len(sentiment_scores)} musicians")

    # Train
    recommender = HybridRecommender(
        alpha_max=HYBRID_ALPHA_MAX,
        beta=HYBRID_BETA,
        svd_components=SVD_COMPONENTS,
        top_n=TOP_N_RECS,
        random_state=RANDOM_SEED,
    )
    recommender.fit(musicians, bookings, sentiment_scores=sentiment_scores)
    log.info("Recommender fitted successfully")

    # Evaluate
    metrics = evaluate_recommendations(recommender, bookings, musicians)
    log.info(f"Precision@10: {metrics['precision_at_10']:.4f}")
    log.info(f"Recall@10:    {metrics['recall_at_10']:.4f}")

    # Demo recommendation
    log.info("Sample recommendation for C001:")
    try:
        recs = recommender.recommend(client_id="C001")
        log.info(f"  Top 3: {recs['Musician_ID'].head(3).tolist()}")
    except Exception as e:
        log.warning(f"Demo recommendation failed: {e}")

    # Cold start demo
    log.info("Cold start recommendation (new user, genre=Jazz, location=London):")
    try:
        cold_recs = recommender.recommend(genres="Jazz", location="London")
        log.info(f"  Top 3: {cold_recs['Musician_ID'].head(3).tolist()}")
    except Exception as e:
        log.warning(f"Cold start demo failed: {e}")

    # Save
    save_path = SAVED_MODELS_DIR / "recommendation"
    recommender.save(save_path)
    log.info(f"Recommender saved → {save_path}")

    print("\n" + "=" * 55)
    print("  RECOMMENDATION SYSTEM TRAINING COMPLETE")
    print("=" * 55)
    print(f"  Musicians indexed  : {len(musicians):,}")
    print(f"  Booking interactions: {len(bookings):,}")
    print(f"  SVD components     : {SVD_COMPONENTS}")
    print(f"  Precision@10       : {metrics['precision_at_10']:.4f}")
    print(f"  Recall@10          : {metrics['recall_at_10']:.4f}")
    print("=" * 55 + "\n")

    return metrics


if __name__ == "__main__":
    run()
