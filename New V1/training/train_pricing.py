"""
BookMyGig — Dynamic Pricing Model Training Script
==================================================
Trains Ridge Regression (baseline) + LightGBM pricing model.
Saves: saved_models/pricing/

Run:  python -m training.train_pricing
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    MUSICIANS_CSV, BOOKINGS_CSV, EVENTS_CSV, SOCIAL_METRICS_CSV,
    PROCESSED_DIR, SAVED_MODELS_DIR, RANDOM_SEED,
)
from models.pricing_model import PricingModel
from utils.feature_engineering import build_pricing_features
from utils.logging_config import get_logger

log = get_logger("train_pricing", "train_pricing.log")


def load_data():
    def _load(clean_name, raw_path):
        c = PROCESSED_DIR / clean_name
        return pd.read_csv(c if c.exists() else raw_path)

    musicians = _load("musicians_clean.csv", MUSICIANS_CSV)
    bookings  = _load("bookings_clean.csv",  BOOKINGS_CSV)
    events    = _load("events_clean.csv",    EVENTS_CSV)
    social    = _load("social_media_metrics_clean.csv", SOCIAL_METRICS_CSV)
    return musicians, bookings, events, social


def run() -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Dynamic Pricing Model Training")
    log.info("=" * 60)

    musicians, bookings, events, social = load_data()
    log.info(f"Musicians: {len(musicians):,} | Bookings: {len(bookings):,} | Events: {len(events):,}")

    # Build feature matrix
    df = build_pricing_features(bookings, musicians, events, social)
    log.info(f"Feature matrix shape: {df.shape}")
    log.info(f"Target (Price_Charged) stats: mean={df['Price_Charged'].mean():.0f} std={df['Price_Charged'].std():.0f}")

    # Train model
    model = PricingModel(random_state=RANDOM_SEED)
    metrics = model.fit(df)

    # Log metrics
    for model_name, m in metrics.items():
        if isinstance(m, dict) and "RMSE" in m:
            log.info(f"[{model_name}] RMSE=£{m['RMSE']:.2f} | MAE=£{m['MAE']:.2f} | R²={m['R2']:.4f}")

    # SHAP explainability (top features)
    log.info("Computing SHAP feature importance...")
    try:
        model.explain(df.sample(min(200, len(df)), random_state=RANDOM_SEED))
    except Exception as e:
        log.warning(f"SHAP explanation failed: {e}")

    # Sample predictions
    sample = df.sample(5, random_state=RANDOM_SEED)
    preds = model.predict(sample)
    log.info("Sample predictions vs actual:")
    for actual, pred in zip(sample["Price_Charged"].values, preds):
        log.info(f"  Actual=£{actual:.0f} | Predicted=£{pred:.0f} | Error=£{abs(actual-pred):.0f}")

    # Save model
    save_path = SAVED_MODELS_DIR / "pricing"
    model.save(save_path)
    log.info(f"Pricing model saved → {save_path}")

    print("\n" + "=" * 60)
    print("  DYNAMIC PRICING MODEL TRAINING COMPLETE")
    print("=" * 60)
    for model_name, m in metrics.items():
        if isinstance(m, dict) and "RMSE" in m:
            print(f"  [{m['model']:20s}]  RMSE=£{m['RMSE']:.2f}  MAE=£{m['MAE']:.2f}  R²={m['R2']:.4f}")
    print("=" * 60 + "\n")

    return metrics


if __name__ == "__main__":
    run()
