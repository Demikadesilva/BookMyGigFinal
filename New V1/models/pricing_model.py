"""
BookMyGig — Dynamic Pricing Model
===================================
Trains two pricing models:
  1. Linear Regression (baseline)
  2. LightGBM Regressor (primary)

Includes SHAP explainability for transparency.

Target: Price_Charged (GBP)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, KFold, cross_val_score

try:
    import lightgbm as lgb
    _LGB_AVAILABLE = True
except ImportError:
    _LGB_AVAILABLE = False

try:
    import shap
    _SHAP_AVAILABLE = True
except ImportError:
    _SHAP_AVAILABLE = False


CATEGORICAL_COLS = ["Event_Type", "City", "Musician_Type"]
NUMERIC_FEATURES = [
    "Expected_Pax", "Duration", "Years_Experience",
    "Base_Price", "Booking_Count", "Followers_total", "Views_total",
]
TARGET = "Price_Charged"
RANDOM_STATE = 42


class PricingModel:
    """Dual-model dynamic pricing with SHAP explainability."""

    def __init__(self, random_state: int = RANDOM_STATE):
        self.random_state = random_state
        self._encoders   = {}
        self._scaler     = StandardScaler()
        self._lr_model   = Ridge(alpha=1.0)
        self._lgb_model  = None
        self._feature_cols = []
        self.is_fitted   = False
        self._metrics    = {}

    # ── preprocessing ─────────────────────────────────────────────────────────

    def _prepare(self, df: pd.DataFrame, fit: bool = False) -> np.ndarray:
        df = df.copy()

        # fill missing numerics
        for col in NUMERIC_FEATURES:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # label-encode categoricals
        for col in CATEGORICAL_COLS:
            if col not in df.columns:
                df[col] = "Unknown"
            if fit:
                le = LabelEncoder()
                df[f"{col}_enc"] = le.fit_transform(df[col].astype(str))
                self._encoders[col] = le
            else:
                if col in self._encoders:
                    le = self._encoders[col]
                    df[f"{col}_enc"] = df[col].astype(str).apply(
                        lambda x: le.transform([x])[0] if x in le.classes_ else -1
                    )
                else:
                    df[f"{col}_enc"] = 0

        feature_cols = NUMERIC_FEATURES + [f"{c}_enc" for c in CATEGORICAL_COLS]
        # only keep columns that exist
        feature_cols = [c for c in feature_cols if c in df.columns]

        if fit:
            self._feature_cols = feature_cols

        X = df[self._feature_cols if not fit else feature_cols].fillna(0).values

        if fit:
            X = self._scaler.fit_transform(X)
        else:
            X = self._scaler.transform(X)

        return X

    # ── training ──────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> dict:
        """Train both models. Returns dict of evaluation metrics."""
        df = df.dropna(subset=[TARGET])
        y = df[TARGET].values

        X = self._prepare(df, fit=True)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=self.random_state
        )

        # ── Linear Regression (Ridge) ─────────────────────────────────────────
        self._lr_model.fit(X_train, y_train)
        y_pred_lr = self._lr_model.predict(X_test)

        lr_metrics = self._score(y_test, y_pred_lr, "linear_regression")

        # ── LightGBM ──────────────────────────────────────────────────────────
        if _LGB_AVAILABLE:
            self._lgb_model = lgb.LGBMRegressor(
                n_estimators=500,
                learning_rate=0.03,
                max_depth=6,
                num_leaves=50,
                min_child_samples=10,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=0.1,
                random_state=self.random_state,
                n_jobs=-1,
                verbose=-1,
            )
            self._lgb_model.fit(
                X_train, y_train,
                eval_set=[(X_test, y_test)],
                callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)],
            )
            y_pred_lgb = self._lgb_model.predict(X_test)
            lgb_metrics = self._score(y_test, y_pred_lgb, "lightgbm")
        else:
            lgb_metrics = {"note": "LightGBM not installed"}

        self.is_fitted = True
        self._metrics  = {"linear_regression": lr_metrics, "lightgbm": lgb_metrics}
        return self._metrics

    @staticmethod
    def _score(y_true: np.ndarray, y_pred: np.ndarray, name: str) -> dict:
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae  = mean_absolute_error(y_true, y_pred)
        r2   = r2_score(y_true, y_pred)
        return {"model": name, "RMSE": round(rmse, 2), "MAE": round(mae, 2), "R2": round(r2, 4)}

    # ── prediction ────────────────────────────────────────────────────────────

    def predict(self, df: pd.DataFrame, use_lgb: bool = True) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model not fitted — call fit() first")
        X = self._prepare(df, fit=False)
        if use_lgb and _LGB_AVAILABLE and self._lgb_model is not None:
            return self._lgb_model.predict(X)
        return self._lr_model.predict(X)

    # ── SHAP explainability ───────────────────────────────────────────────────

    def explain(self, df: pd.DataFrame, max_display: int = 15) -> None:
        """Print SHAP summary for LightGBM model."""
        if not _SHAP_AVAILABLE:
            print("SHAP not installed: pip install shap")
            return
        if self._lgb_model is None:
            print("LightGBM model not trained — cannot explain.")
            return
        X = self._prepare(df, fit=False)
        explainer  = shap.TreeExplainer(self._lgb_model)
        shap_vals  = explainer.shap_values(X)
        print("\nSHAP Feature Importance (mean |SHAP value|):")
        importances = np.abs(shap_vals).mean(axis=0)
        for feat, imp in sorted(zip(self._feature_cols, importances), key=lambda x: -x[1])[:max_display]:
            bar = "#" * int(imp / importances.max() * 20)
            print(f"  {feat:<35} {bar} {imp:.2f}")

    # ── persistence ───────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._lr_model,    path / "ridge_pricing_model.joblib")
        joblib.dump(self._scaler,      path / "pricing_scaler.joblib")
        joblib.dump(self._encoders,    path / "pricing_encoders.joblib")
        joblib.dump(self._feature_cols,path / "pricing_feature_cols.joblib")
        if self._lgb_model is not None:
            joblib.dump(self._lgb_model, path / "lightgbm_pricing_model.joblib")

    @classmethod
    def load(cls, path: str | Path) -> "PricingModel":
        path = Path(path)
        obj = cls()
        obj._lr_model    = joblib.load(path / "ridge_pricing_model.joblib")
        obj._scaler      = joblib.load(path / "pricing_scaler.joblib")
        obj._encoders    = joblib.load(path / "pricing_encoders.joblib")
        obj._feature_cols= joblib.load(path / "pricing_feature_cols.joblib")
        lgb_path = path / "lightgbm_pricing_model.joblib"
        if lgb_path.exists():
            obj._lgb_model = joblib.load(lgb_path)
        obj.is_fitted = True
        return obj
