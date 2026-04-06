"""
BookMyGig — Pricing Model Evaluation
======================================
Metrics: RMSE, MAE, R², MAPE, residual analysis

Run:  python -m evaluation.evaluate_pricing
"""
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    PROCESSED_DIR, MUSICIANS_CSV, BOOKINGS_CSV, EVENTS_CSV,
    SOCIAL_METRICS_CSV, SAVED_MODELS_DIR, EVAL_REPORT_DIR, RANDOM_SEED,
)
from models.pricing_model import PricingModel
from utils.feature_engineering import build_pricing_features
from utils.logging_config import get_logger

log = get_logger("eval_pricing", "eval_pricing.log")


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    return np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100


def evaluate() -> dict:
    log.info("=" * 60)
    log.info("BookMyGig — Pricing Model Evaluation")
    log.info("=" * 60)

    # Load data
    def _load(clean, raw):
        c = PROCESSED_DIR / clean
        return pd.read_csv(c if c.exists() else raw)

    musicians = _load("musicians_clean.csv", MUSICIANS_CSV)
    bookings  = _load("bookings_clean.csv",  BOOKINGS_CSV)
    events    = _load("events_clean.csv",    EVENTS_CSV)
    social    = _load("social_media_metrics_clean.csv", SOCIAL_METRICS_CSV)

    df = build_pricing_features(bookings, musicians, events, social)
    df = df.dropna(subset=["Price_Charged"])

    _, test_df = train_test_split(df, test_size=0.2, random_state=RANDOM_SEED)

    # Load or retrain model
    model_path = SAVED_MODELS_DIR / "pricing"
    if model_path.exists():
        model = PricingModel.load(model_path)
    else:
        log.warning("Pricing model not found — training now...")
        from training.train_pricing import run
        run()
        model = PricingModel.load(model_path)

    y_true = test_df["Price_Charged"].values

    # Evaluate both models
    results = {}
    for use_lgb, name in [(False, "Ridge Regression"), (True, "LightGBM")]:
        try:
            y_pred = model.predict(test_df, use_lgb=use_lgb)
            rmse_val = np.sqrt(mean_squared_error(y_true, y_pred))
            mae_val  = mean_absolute_error(y_true, y_pred)
            r2_val   = r2_score(y_true, y_pred)
            mape_val = mape(y_true, y_pred)
            
            residuals = y_true - y_pred
            mean_res = np.mean(residuals)
            max_res = np.max(residuals)
            min_res = np.min(residuals)
            
            results[name] = {
                "RMSE":  round(rmse_val, 2),
                "MAE":   round(mae_val, 2),
                "R2":    round(r2_val, 4),
                "MAPE":  round(mape_val, 2),
                "Mean_Residual": round(mean_res, 2),
                "Max_Residual": round(max_res, 2),
                "Min_Residual": round(min_res, 2),
            }
            log.info(f"[{name}] RMSE=£{rmse_val:.2f} MAE=£{mae_val:.2f} R²={r2_val:.4f} MAPE={mape_val:.1f}%")
        except Exception as e:
            results[name] = {"error": str(e)}
            log.warning(f"[{name}] failed: {e}")

    metrics = {"test_size": len(test_df), "models": results}

    print("\n" + "=" * 65)
    print("  PRICING MODEL EVALUATION RESULTS")
    print("=" * 65)
    print(f"  Test set size : {len(test_df)}")
    print(f"  {'Model':<18} {'RMSE':>7} {'MAE':>7} {'R²':>7} {'MAPE':>7} {'Mean Res':>9} {'Max Res':>8}")
    print("-" * 75)
    for name, res in results.items():
        if "error" not in res:
            print(f"  {name:<18} £{res['RMSE']:>6.2f} £{res['MAE']:>6.2f} {res['R2']:>7.4f} {res['MAPE']:>6.1f}% "
                  f"£{res['Mean_Residual']:>8.2f} £{res['Max_Residual']:>7.2f} £{res['Min_Residual']:>7.2f}")
    print("=" * 65 + "\n")

    report_path = EVAL_REPORT_DIR / "pricing_evaluation.json"
    with open(report_path, "w") as fp:
        json.dump(metrics, fp, indent=2)
    log.info(f"Report saved → {report_path}")
    return metrics


if __name__ == "__main__":
    evaluate()
