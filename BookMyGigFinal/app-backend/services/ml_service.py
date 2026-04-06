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
)


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

        self._recommender_tfidf = None
        self._recommender_tfidf_mat = None
        self._recommender_svd = None
        self._recommender_user_item = None
        self._recommender_cf_preds = None
        self._recommender_musicians = None
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
        if self._recommender_tfidf is not None:
            return
        p = RECOMMENDATION_MODEL_PATH
        self._recommender_config = joblib.load(p / "recommender_config.joblib")
        self._recommender_tfidf = joblib.load(p / "tfidf_vectorizer.joblib")
        self._recommender_tfidf_mat = joblib.load(p / "tfidf_matrix.joblib")
        self._recommender_svd = joblib.load(p / "svd_model.joblib")
        self._recommender_user_item = joblib.load(p / "user_item_matrix.joblib")
        self._recommender_cf_preds = joblib.load(p / "cf_predictions.joblib")
        self._recommender_musicians = joblib.load(p / "musicians_index.joblib")
        print("[ML] Recommendation model loaded ✓")

    def get_recommendations(
        self,
        client_id: str | None = None,
        genres: str | None = None,
        location: str | None = None,
        top_n: int = 10,
    ) -> list[dict]:
        """Get recommended musicians for a client."""
        self._load_recommendation()

        cfg = self._recommender_config
        alpha_max = cfg.get("alpha_max", 0.7)
        beta = cfg.get("beta", 0.2)

        from sklearn.metrics.pairwise import cosine_similarity

        musicians = self._recommender_musicians

        # CBF scores
        query_text = f"{genres or ''} {location or ''}".strip() or "pop"
        query_vec = self._recommender_tfidf.transform([query_text])
        cbf = cosine_similarity(query_vec, self._recommender_tfidf_mat).flatten()
        cbf_series = pd.Series(cbf, index=musicians.index)

        # CF scores
        alpha = 0.0
        cf_norm = pd.Series(0.0, index=musicians.index)
        if client_id and self._recommender_user_item is not None and client_id in self._recommender_user_item.index:
            rated = (self._recommender_user_item.loc[client_id] > 0).sum()
            alpha = min(rated / 10, alpha_max)
            if alpha > 0:
                cf_raw = self._recommender_cf_preds.loc[client_id].reindex(musicians.index).fillna(0)
                cf_norm = (cf_raw - cf_raw.min()) / (cf_raw.max() - cf_raw.min() + 1e-8)

        hybrid = alpha * cf_norm + (1 - alpha) * cbf_series

        # Sentiment boost
        sent = musicians.get("avg_sentiment", pd.Series(0.5, index=musicians.index))
        hybrid = hybrid * (1 + beta * sent.reindex(musicians.index).fillna(0.5))

        result = pd.DataFrame({
            "Musician_ID": hybrid.index,
            "final_score": hybrid.values,
            "cbf_score": cbf_series.values,
            "cf_score": cf_norm.values,
            "sentiment_boost": sent.reindex(hybrid.index).fillna(0.5).values,
        })

        # Merge musician details
        musician_details = musicians[["Musician_Name", "Musician_Type", "Genres", "Location", "Base_Price"]].reset_index()
        result = result.merge(musician_details, on="Musician_ID", how="left")
        result = result.sort_values("final_score", ascending=False).head(top_n).reset_index(drop=True)

        return result.rename(columns={
            "Musician_ID": "musician_id",
            "Musician_Name": "musician_name",
            "Musician_Type": "musician_type",
            "Genres": "genres",
            "Location": "location",
            "Base_Price": "base_price",
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
