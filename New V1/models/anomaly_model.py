"""
BookMyGig — Review Anomaly Detection Model
===========================================
Uses Isolation Forest to flag suspicious reviews where the review text
sentiment is inconsistent with the numeric rating (fake reviews).

Features used:
  - Rating (1-5)
  - Review_Length (word count)
  - Sentiment_Score (0-1 from SentimentModel)
  - Sentiment_Rating_Gap = |expected_sentiment - Sentiment_Score|
  - Avg_Musician_Rating   (historical musician avg)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix


FEATURE_COLS = [
    "Rating",
    "Review_Length",
    "Sentiment_Score",
    "Sentiment_Rating_Gap",
    "Avg_Musician_Rating",
]

CONTAMINATION = 0.08
N_ESTIMATORS  = 200
RANDOM_STATE  = 42


class AnomalyModel:
    """Isolation Forest wrapper for review anomaly detection."""

    def __init__(
        self,
        contamination: float = CONTAMINATION,
        n_estimators: int = N_ESTIMATORS,
        random_state: int = RANDOM_STATE,
    ):
        self.contamination = contamination
        self.n_estimators  = n_estimators
        self.random_state  = random_state
        self.model   = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1,
            random_state=random_state,
        )
        self.scaler  = StandardScaler()
        self.is_fitted = False

    # ── feature engineering ───────────────────────────────────────────────────

    @staticmethod
    def build_features(df: pd.DataFrame) -> pd.DataFrame:
        """
        Expects df to have: Rating, Review_Text, Sentiment_Score, Avg_Musician_Rating
        Returns enriched DataFrame with all FEATURE_COLS present.
        """
        df = df.copy()
        df["Rating"]         = pd.to_numeric(df["Rating"], errors="coerce").fillna(3)
        df["Review_Length"]  = df["Review_Text"].fillna("").apply(lambda x: len(str(x).split()))
        df["Sentiment_Score"]= pd.to_numeric(df.get("Sentiment_Score", pd.Series([0.5]*len(df))), errors="coerce").fillna(0.5)

        # expected sentiment from numeric rating (1→0, 5→1)
        expected = (df["Rating"] - 1) / 4
        df["Sentiment_Rating_Gap"] = (expected - df["Sentiment_Score"]).abs()

        if "Avg_Musician_Rating" not in df.columns:
            df["Avg_Musician_Rating"] = df["Rating"].mean()

        return df

    # ── training ──────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame) -> "AnomalyModel":
        df = self.build_features(df)
        X = df[FEATURE_COLS].fillna(0).values
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
        return self

    # ── prediction ────────────────────────────────────────────────────────────

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Returns original df with added columns:
          anomaly_score : lower = more anomalous
          is_anomaly    : True if flagged
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted — call fit() first")
        df = self.build_features(df)
        X = df[FEATURE_COLS].fillna(0).values
        X_scaled = self.scaler.transform(X)
        scores = self.model.decision_function(X_scaled)
        labels = self.model.predict(X_scaled)  # -1 = anomaly, 1 = normal
        df["anomaly_score"] = np.round(scores, 4)
        df["is_anomaly"]    = labels == -1
        return df

    def predict_flag(self, df: pd.DataFrame) -> pd.Series:
        """Returns boolean Series: True = anomalous review."""
        return self.predict(df)["is_anomaly"]

    # ── evaluation ────────────────────────────────────────────────────────────

    def evaluate(self, df: pd.DataFrame, true_labels: pd.Series | None = None) -> dict:
        result = self.predict(df)
        n_flagged = result["is_anomaly"].sum()
        n_total   = len(result)
        flagged_pct = n_flagged / n_total * 100

        metrics = {
            "total_reviews":   n_total,
            "flagged_anomalies": int(n_flagged),
            "flagged_pct":     round(flagged_pct, 2),
            "avg_anomaly_score": round(result["anomaly_score"].mean(), 4),
        }

        if true_labels is not None:
            y_pred = result["is_anomaly"].astype(int)
            y_true = true_labels.astype(int)
            metrics["classification_report"] = classification_report(y_true, y_pred, output_dict=True)
            metrics["confusion_matrix"] = confusion_matrix(y_true, y_pred).tolist()

        return metrics

    # ── persistence ───────────────────────────────────────────────────────────

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model,  path / "isolation_forest.joblib")
        joblib.dump(self.scaler, path / "anomaly_scaler.joblib")
        joblib.dump({
            "contamination": self.contamination,
            "n_estimators":  self.n_estimators,
            "random_state":  self.random_state,
        }, path / "anomaly_config.joblib")

    @classmethod
    def load(cls, path: str | Path) -> "AnomalyModel":
        path = Path(path)
        cfg = joblib.load(path / "anomaly_config.joblib")
        obj = cls(**cfg)
        obj.model     = joblib.load(path / "isolation_forest.joblib")
        obj.scaler    = joblib.load(path / "anomaly_scaler.joblib")
        obj.is_fitted = True
        return obj
