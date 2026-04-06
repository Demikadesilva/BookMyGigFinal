"""
Database Seeder — Populates the database from CSV files on first run.
Also runs sentiment analysis and anomaly detection on all reviews.
"""
import pandas as pd
from sqlalchemy.orm import Session

from config import RAW_DATA_DIR
from database import SessionLocal
from models.musician import Musician
from models.event import Event
from models.booking import Booking
from models.review import Review
from models.social_metric import SocialMetric


def seed_database():
    """Seed all tables from CSV files if they are empty."""
    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(Musician).count() > 0:
            print("[SEED] Database already seeded, skipping.")
            return

        print("[SEED] Starting database seed from CSV files...")

        # ── Musicians ─────────────────────────────────────────────────────────
        df = pd.read_csv(RAW_DATA_DIR / "musicians.csv")
        for _, row in df.iterrows():
            db.add(Musician(
                musician_id=row["Musician_ID"],
                name=row["Musician_Name"],
                musician_type=row["Musician_Type"],
                contact=row.get("Musician_Contact", ""),
                location=row.get("Location", ""),
                genres=row.get("Genres", ""),
                years_experience=int(row.get("Years_Experience", 0)),
                base_price=float(row.get("Base_Price", 0)),
                has_social_links=str(row.get("Social_Links", "")).lower() == "true",
            ))
        db.commit()
        print(f"  → {len(df)} musicians seeded ✓")

        # ── Events ────────────────────────────────────────────────────────────
        df = pd.read_csv(RAW_DATA_DIR / "events.csv")
        for _, row in df.iterrows():
            db.add(Event(
                event_id=row["Event_ID"],
                client_id=row["Client_ID"],
                city=row.get("City", ""),
                date_time=str(row.get("Date_Time", "")),
                expected_pax=int(row.get("Expected_Pax", 0)),
                event_type=row.get("Event_Type", ""),
                budget=float(row.get("Budget", 0)),
            ))
        db.commit()
        print(f"  → {len(df)} events seeded ✓")

        # ── Bookings ──────────────────────────────────────────────────────────
        df = pd.read_csv(RAW_DATA_DIR / "bookings.csv")
        for _, row in df.iterrows():
            db.add(Booking(
                booking_id=row["Booking_ID"],
                musician_id=row["Musician_ID"],
                client_id=row["Client_ID"],
                event_id=row["Event_ID"],
                date_time=str(row.get("Date_Time", "")),
                duration=int(row.get("Duration", 1)),
                price_charged=float(row.get("Price_Charged", 0)),
                rating=int(row.get("Rating", 0)),
            ))
        db.commit()
        print(f"  → {len(df)} bookings seeded ✓")

        # ── Reviews (with ML analysis) ────────────────────────────────────────
        from services.ml_service import MLService
        ml = MLService.get_instance()

        df = pd.read_csv(RAW_DATA_DIR / "reviews.csv")
        for _, row in df.iterrows():
            text = str(row.get("Review_Text", ""))
            rating = int(row.get("Rating", 3))

            # Sentiment analysis
            sentiment = ml.analyze_sentiment(text)

            # Get avg musician rating for anomaly detection
            booking = db.query(Booking).filter(Booking.booking_id == row["Booking_ID"]).first()
            avg_musician_rating = 3.5
            if booking:
                from sqlalchemy import func
                avg_r = db.query(func.avg(Booking.rating)).filter(
                    Booking.musician_id == booking.musician_id
                ).scalar()
                if avg_r:
                    avg_musician_rating = float(avg_r)

            anomaly = ml.detect_anomaly(
                rating=rating,
                review_text=text,
                sentiment_score=sentiment["sentiment_score"],
                avg_musician_rating=avg_musician_rating,
            )

            db.add(Review(
                review_id=row["Review_ID"],
                booking_id=row["Booking_ID"],
                review_text=text,
                rating=rating,
                created_at=str(row.get("Created_At", "")),
                sentiment_score=sentiment["sentiment_score"],
                sentiment_label=sentiment["sentiment_label"],
                vader_score=sentiment["vader_score"],
                bert_score=sentiment.get("bert_score"),
                is_anomaly=anomaly["is_anomaly"],
                anomaly_score=anomaly["anomaly_score"],
            ))

        db.commit()
        print(f"  → {len(df)} reviews seeded (with sentiment + anomaly analysis) ✓")

        # ── Social Media Metrics ──────────────────────────────────────────────
        df = pd.read_csv(RAW_DATA_DIR / "social_media_metrics.csv")
        for _, row in df.iterrows():
            db.add(SocialMetric(
                musician_id=row["Musician_ID"],
                platform=row.get("Platform", ""),
                followers=int(row.get("Followers", 0)),
                likes=int(row.get("Likes", 0)),
                views=int(row.get("Views", 0)),
                date_collected=str(row.get("Date_Collected", "")),
            ))
        db.commit()
        print(f"  → {len(df)} social metrics seeded ✓")

        print("[SEED] Database seeding complete! ✓")

    except Exception as e:
        db.rollback()
        print(f"[SEED] Error seeding database: {e}")
        raise
    finally:
        db.close()
