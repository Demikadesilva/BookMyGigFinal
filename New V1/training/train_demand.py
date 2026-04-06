"""
BookMyGig — Demand Forecasting Training Script
===============================================
Trains LightGBM demand forecasting model on weekly booking data.
Saves: saved_models/demand/

Run:  python -m training.train_demand
"""

import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import BOOKINGS_CSV, PROCESSED_DIR, SAVED_MODELS_DIR, RANDOM_SEED
from models.demand_model import DemandForecastModel
from utils.logging_config import get_logger

log = get_logger("train_demand", "train_demand.log")


def run() -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Demand Forecasting Training")
    log.info("=" * 60)

    b_clean = PROCESSED_DIR / "bookings_clean.csv"
    bookings = pd.read_csv(b_clean if b_clean.exists() else BOOKINGS_CSV)
    log.info(f"Bookings loaded: {len(bookings):,}")

    model = DemandForecastModel(random_state=RANDOM_SEED)

    # Build weekly series for inspection
    weekly = model.build_weekly_demand(bookings)
    log.info(f"Weekly demand series: {len(weekly)} weeks ({weekly['demand'].min()}–{weekly['demand'].max()} bookings/week)")

    # Train
    metrics = model.fit(bookings)
    log.info(f"RMSE: {metrics['rmse']} | MAE: {metrics['mae']} | R²: {metrics['r2']}")
    log.info(f"CV RMSE: {metrics['cv_rmse_mean']} ± {metrics['cv_rmse_std']}")

    # Save model
    save_path = SAVED_MODELS_DIR / "demand"
    model.save(save_path)
    log.info(f"Demand model saved → {save_path}")

    print("\n" + "=" * 55)
    print("  DEMAND FORECASTING TRAINING COMPLETE")
    print("=" * 55)
    print(f"  Weeks in dataset   : {len(weekly)}")
    print(f"  Avg weekly demand  : {weekly['demand'].mean():.1f} bookings")
    print(f"  RMSE               : {metrics['rmse']}")
    print(f"  MAE                : {metrics['mae']}")
    print(f"  R²                 : {metrics['r2']}")
    print(f"  CV RMSE            : {metrics['cv_rmse_mean']} ± {metrics['cv_rmse_std']}")
    print("=" * 55 + "\n")

    return metrics


if __name__ == "__main__":
    run()
