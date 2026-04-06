"""
Feature engineering utilities for BookMyGig ML pipeline.
Builds enriched features from the 6 raw tables.
"""

import numpy as np
import pandas as pd


def build_musician_features(
    musicians: pd.DataFrame,
    bookings: pd.DataFrame,
    reviews: pd.DataFrame,
    social: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate per-musician statistics into a feature-rich DataFrame."""

    # ── booking-level aggregations ────────────────────────────────────────────
    bk_agg = (
        bookings.groupby("Musician_ID")
        .agg(
            Booking_Count=("Booking_ID", "count"),
            Avg_Price_Charged=("Price_Charged", "mean"),
            Total_Revenue=("Price_Charged", "sum"),
            Avg_Rating=("Rating", "mean"),
            Avg_Duration=("Duration", "mean"),
        )
        .reset_index()
    )

    # ── review-level aggregations ─────────────────────────────────────────────
    # join reviews → bookings to get Musician_ID
    rv = reviews.merge(bookings[["Booking_ID", "Musician_ID"]], on="Booking_ID", how="left")
    rv_agg = (
        rv.groupby("Musician_ID")
        .agg(
            Review_Count=("Review_ID", "count"),
            Avg_Review_Rating=("Rating", "mean"),
            Avg_Sentiment_Score=("Sentiment_Score", "mean") if "Sentiment_Score" in rv.columns else ("Rating", "mean"),
        )
        .reset_index()
    )

    # ── social media aggregations ─────────────────────────────────────────────
    sc_agg = (
        social.groupby("Musician_ID")
        .agg(
            Followers_total=("Followers", "sum"),
            Likes_total=("Likes", "sum"),
            Views_total=("Views", "sum"),
        )
        .reset_index()
    )

    # ── merge everything ──────────────────────────────────────────────────────
    df = musicians.copy()
    df = df.merge(bk_agg, on="Musician_ID", how="left")
    df = df.merge(rv_agg, on="Musician_ID", how="left")
    df = df.merge(sc_agg, on="Musician_ID", how="left")

    # ── derived features ──────────────────────────────────────────────────────
    df["Booking_Count"]  = df["Booking_Count"].fillna(0)
    df["Price_Premium"]  = (df["Avg_Price_Charged"].fillna(0) / df["Base_Price"].replace(0, 1)) - 1
    df["Engagement_Rate"] = (
        (df["Likes_total"].fillna(0) + df["Views_total"].fillna(0))
        / df["Followers_total"].replace(0, 1).fillna(1)
    )
    df["Is_Cold_Start"]  = (df["Booking_Count"] == 0).astype(int)
    df["Popularity_Score"] = (
        0.4 * df["Avg_Rating"].fillna(0)
        + 0.3 * np.log1p(df["Booking_Count"].fillna(0))
        + 0.2 * np.log1p(df["Followers_total"].fillna(0))
        + 0.1 * df["Years_Experience"] / 25
    )

    return df


def build_pricing_features(
    bookings: pd.DataFrame,
    musicians: pd.DataFrame,
    events: pd.DataFrame,
    social: pd.DataFrame,
) -> pd.DataFrame:
    """Build feature matrix for pricing model."""

    sc_agg = (
        social.groupby("Musician_ID")
        .agg(Followers_total=("Followers", "sum"), Views_total=("Views", "sum"))
        .reset_index()
    )

    bk_agg = (
        bookings.groupby("Musician_ID")
        .agg(Booking_Count=("Booking_ID", "count"), Avg_Rating=("Rating", "mean"))
        .reset_index()
    )

    df = bookings.merge(musicians, on="Musician_ID", how="left")
    df = df.merge(events[["Event_ID", "Expected_Pax", "Event_Type", "City", "Budget"]], on="Event_ID", how="left")
    df = df.merge(sc_agg, on="Musician_ID", how="left")
    df = df.merge(bk_agg, on="Musician_ID", how="left")

    df["Followers_total"] = df["Followers_total"].fillna(0)
    df["Views_total"]     = df["Views_total"].fillna(0)
    df["Booking_Count"]   = df["Booking_Count"].fillna(0)

    return df


def build_review_features(reviews: pd.DataFrame, bookings: pd.DataFrame) -> pd.DataFrame:
    """Attach extra fields to review DataFrame for anomaly detection."""
    df = reviews.copy()
    df["Review_Length"] = df["Review_Text"].fillna("").apply(lambda x: len(str(x).split()))

    # merge avg musician rating
    m_avg = (
        bookings.groupby("Musician_ID")["Rating"]
        .mean()
        .rename("Avg_Musician_Rating")
        .reset_index()
    )
    df = df.merge(bookings[["Booking_ID", "Musician_ID"]], on="Booking_ID", how="left")
    df = df.merge(m_avg, on="Musician_ID", how="left")
    df["Avg_Musician_Rating"] = df["Avg_Musician_Rating"].fillna(df["Rating"].mean())

    return df
