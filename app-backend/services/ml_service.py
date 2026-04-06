"""
ML Service — Lazy-loads and exposes all 5 trained models.
"""
from __future__ import annotations

import sys
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Optional, Dict, List, Any

from config import (
    PRICING_MODEL_PATH,
    ANOMALY_MODEL_PATH,
    RECOMMENDATION_MODEL_PATH,
    DEMAND_MODEL_PATH,
    SENTIMENT_MODEL_PATH,
    RAW_DATA_DIR,
    PROJECT_ROOT,
)

import importlib.util

# Load the HybridRecommender class from its file directly to avoid path conflicts
MODELS_DIR = PROJECT_ROOT / "New V1" / "models"
spec = importlib.util.spec_from_file_location("recommendation_model", str(MODELS_DIR / "recommendation_model.py"))
rec_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec_mod)
HybridRecommender = rec_mod.HybridRecommender


class MLService:
    """Singleton-style service that lazy-loads all ML models."""

    _instance: Optional["MLService"] = None

    def __init__(self):
        self._pricing_model = None
        self._pricing_scaler = None
        self._pricing_encoders = None
        self._pricing_feature_cols = None
        self._pricing_lgb = None

        self._anomaly_model = None
        self._anomaly_scaler = None

        self._recommender = None
        self._recommender_config = None

        self._demand_model = None
        self._demand_feature_cols = None

        self._sentiment_vader = None
        self._sentiment_use_bert = False

        # Raw data cache
        self._bookings_df = None
        self._musicians_df = None
        self._events_df = None
        self._reviews_df = None
        self._social_df = None

    @classmethod
    def get_instance(cls) -> "MLService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ═══════════════════════════════════════════════════════════════════════════
    # Raw Data Loading
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_raw_data(self):
        if self._bookings_df is not None:
            return
        self._bookings_df = pd.read_csv(RAW_DATA_DIR / "bookings.csv")
        self._musicians_df = pd.read_csv(RAW_DATA_DIR / "musicians.csv")
        self._events_df = pd.read_csv(RAW_DATA_DIR / "events.csv")
        self._reviews_df = pd.read_csv(RAW_DATA_DIR / "reviews.csv")
        self._social_df = pd.read_csv(RAW_DATA_DIR / "social_media_metrics.csv")

    # ═══════════════════════════════════════════════════════════════════════════
    # 1. PRICING MODEL (LightGBM)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_pricing(self):
        if self._pricing_lgb is not None:
            return
        p = PRICING_MODEL_PATH
        self._pricing_lgb = joblib.load(p / "lightgbm_pricing_model.joblib")
        self._pricing_scaler = joblib.load(p / "pricing_scaler.joblib")
        self._pricing_encoders = joblib.load(p / "pricing_encoders.joblib")
        self._pricing_feature_cols = joblib.load(p / "pricing_feature_cols.joblib")
        print("[ML] Pricing model loaded ✓")

    def predict_price(self, data: dict) -> dict:
        """
        Predict price. Expected keys:
            Event_Type, City, Musician_Type, Expected_Pax, Duration,
            Years_Experience, Base_Price, Booking_Count, Followers_total, Views_total
        """
        self._load_pricing()

        NUMERIC_FEATURES = [
            "Expected_Pax", "Duration", "Years_Experience",
            "Base_Price", "Booking_Count", "Followers_total", "Views_total",
        ]
        CATEGORICAL_COLS = ["Event_Type", "City", "Musician_Type"]

        df = pd.DataFrame([data])

        # Fill defaults
        for col in NUMERIC_FEATURES:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        # Encode categoricals
        for col in CATEGORICAL_COLS:
            if col not in df.columns:
                df[col] = "Unknown"
            if col in self._pricing_encoders:
                le = self._pricing_encoders[col]
                df[f"{col}_enc"] = df[col].astype(str).apply(
                    lambda x: le.transform([x])[0] if x in le.classes_ else -1
                )
            else:
                df[f"{col}_enc"] = 0

        feature_cols = self._pricing_feature_cols
        for c in feature_cols:
            if c not in df.columns:
                df[c] = 0

        X = df[feature_cols].fillna(0).values
        X = self._pricing_scaler.transform(X)
        prediction = self._pricing_lgb.predict(X)[0]

        return {
            "estimated_price": round(float(max(prediction, 0)), 2),
            "model_used": "LightGBM",
            "features_used": data,
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # 2. SENTIMENT ANALYSIS (VADER + optional DistilBERT)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_sentiment(self):
        if self._sentiment_vader is not None:
            return
        try:
            from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
            self._sentiment_vader = SentimentIntensityAnalyzer()
            print("[ML] VADER sentiment loaded ✓")
        except ImportError:
            print("[ML] VADER not available, using fallback")
            self._sentiment_vader = None

    def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment of a single text."""
        self._load_sentiment()

        # VADER score
        if self._sentiment_vader:
            compound = self._sentiment_vader.polarity_scores(text)["compound"]
            vader_score = (compound + 1) / 2  # normalise to [0, 1]
        else:
            vader_score = 0.5

        # Use VADER-only blend for now (BERT is optional/heavy)
        sentiment_score = vader_score

        if sentiment_score >= 0.6:
            label = "POSITIVE"
        elif sentiment_score <= 0.4:
            label = "NEGATIVE"
        else:
            label = "NEUTRAL"

        return {
            "text": text,
            "vader_score": round(vader_score, 4),
            "bert_score": None,
            "sentiment_score": round(sentiment_score, 4),
            "sentiment_label": label,
        }

    def analyze_sentiment_batch(self, texts: list[str]) -> list[dict]:
        return [self.analyze_sentiment(t) for t in texts]

    # ═══════════════════════════════════════════════════════════════════════════
    # 3. ANOMALY DETECTION (Isolation Forest)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_anomaly(self):
        if self._anomaly_model is not None:
            return
        p = ANOMALY_MODEL_PATH
        self._anomaly_model = joblib.load(p / "isolation_forest.joblib")
        self._anomaly_scaler = joblib.load(p / "anomaly_scaler.joblib")
        print("[ML] Anomaly model loaded ✓")

    def detect_anomaly(self, rating: int, review_text: str, sentiment_score: float, avg_musician_rating: float = 3.5) -> dict:
        """Check if a single review is anomalous."""
        self._load_anomaly()

        review_length = len(review_text.split()) if review_text else 0
        expected = (rating - 1) / 4
        sentiment_rating_gap = abs(expected - sentiment_score)

        features = np.array([[
            rating, review_length, sentiment_score,
            sentiment_rating_gap, avg_musician_rating
        ]])

        features_scaled = self._anomaly_scaler.transform(features)
        score = self._anomaly_model.decision_function(features_scaled)[0]
        label = self._anomaly_model.predict(features_scaled)[0]

        return {
            "is_anomaly": bool(label == -1),
            "anomaly_score": round(float(score), 4),
            "features": {
                "Rating": rating,
                "Review_Length": review_length,
                "Sentiment_Score": sentiment_score,
                "Sentiment_Rating_Gap": round(sentiment_rating_gap, 4),
                "Avg_Musician_Rating": avg_musician_rating,
            }
        }

    # ═══════════════════════════════════════════════════════════════════════════
    # 4. RECOMMENDATION (Hybrid CBF + CF)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_recommendation(self):
        if self._recommender is not None:
            return
        p = RECOMMENDATION_MODEL_PATH
        self._recommender = HybridRecommender.load(p)
        print("[ML] Recommendation model loaded (V1 Hybrid) [OK]")

    def get_recommendations(
        self,
        client_id: str | None = None,
        genres: str | None = None,
        location: str | None = None,
        top_n: int = 10,
    ) -> list[dict]:
        """Get recommended musicians for a client."""
        self._load_recommendation()
        
        # Call the dedicated recommendation method from the model class
        recs_df = self._recommender.recommend(
            client_id=client_id,
            genres=genres,
            location=location
        )
        
        # Map to the keys expected by the frontend
        return recs_df.head(top_n).rename(columns={
            "Musician_ID": "musician_id",
            "Musician_Name": "name",
            "Musician_Type": "type",
            "Genres": "genres",
            "Location": "location",
            "Base_Price": "base_price",
            # final_score, cbf_score, sentiment_boost are already in recs_df
        }).to_dict(orient="records")

    # ═══════════════════════════════════════════════════════════════════════════
    # 5. DEMAND FORECASTING (LightGBM time-series)
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_demand(self):
        if self._demand_model is not None:
            return
        p = DEMAND_MODEL_PATH
        self._demand_model = joblib.load(p / "demand_model.joblib")
        self._demand_feature_cols = joblib.load(p / "demand_feature_cols.joblib")
        print("[ML] Demand model loaded ✓")

    def get_demand_history(self, city: str | None = None) -> list[dict]:
        """Get weekly demand history from the booking data."""
        self._load_raw_data()

        df = self._bookings_df.copy()
        df["Date_Time"] = pd.to_datetime(df["Date_Time"], errors="coerce")
        df = df.dropna(subset=["Date_Time"])

        # If city filter, join with events
        if city:
            events = self._events_df[["Event_ID", "City"]].copy()
            df = df.merge(events, on="Event_ID", how="left")
            df = df[df["City"].str.lower() == city.lower()]

        df["week"] = df["Date_Time"].dt.to_period("W").dt.start_time

        weekly = (
            df.groupby("week")
            .agg(
                demand=("Booking_ID", "count"),
                avg_price=("Price_Charged", "mean"),
                avg_rating=("Rating", "mean"),
            )
            .reset_index()
            .sort_values("week")
        )

        result = []
        for _, row in weekly.iterrows():
            result.append({
                "week": row["week"].strftime("%Y-%m-%d"),
                "demand": int(row["demand"]),
                "avg_price": round(float(row["avg_price"]), 2),
                "avg_rating": round(float(row["avg_rating"]), 2),
            })

        return result

    def get_cities(self) -> list[str]:
        self._load_raw_data()
        return sorted(self._events_df["City"].dropna().unique().tolist())