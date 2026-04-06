"""
AI Router — All ML model demo endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.review import Review
from schemas import (
    PriceEstimateRequest, PriceEstimateResponse,
    SentimentRequest, SentimentResponse,
    RecommendationResponse, AnomalyStatsResponse,
    ReviewResponse, DashboardStats,
)
from models.musician import Musician
from models.booking import Booking
from models.event import Event
from services.ml_service import MLService

router = APIRouter(prefix="/ai", tags=["AI Models"])


# ─── PRICE ESTIMATION ────────────────────────────────────────────────────────

@router.post("/price-estimate", response_model=PriceEstimateResponse)
def estimate_price(req: PriceEstimateRequest):
    ml = MLService.get_instance()
    result = ml.predict_price({
        "Event_Type": req.event_type,
        "City": req.city,
        "Musician_Type": req.musician_type,
        "Expected_Pax": req.expected_pax,
        "Duration": req.duration,
        "Years_Experience": req.years_experience,
        "Base_Price": req.base_price,
        "Booking_Count": 5,  # default estimate
        "Followers_total": 1000,
        "Views_total": 5000,
    })
    return result


# ─── SENTIMENT ANALYSIS DEMO ─────────────────────────────────────────────────

@router.post("/sentiment", response_model=SentimentResponse)
def analyze_sentiment(req: SentimentRequest):
    ml = MLService.get_instance()
    return ml.analyze_sentiment(req.text)


# ─── RECOMMENDATIONS ─────────────────────────────────────────────────────────

@router.get("/recommendations")
def get_recommendations(
    client_id: str = Query(None),
    genres: str = Query(None),
    location: str = Query(None),
    top_n: int = Query(10, ge=1, le=50),
):
    ml = MLService.get_instance()
    return ml.get_recommendations(
        client_id=client_id,
        genres=genres,
        location=location,
        top_n=top_n,
    )


# ─── DEMAND FORECAST ─────────────────────────────────────────────────────────

@router.get("/demand")
def get_demand(city: str = Query(None)):
    ml = MLService.get_instance()
    return ml.get_demand_history(city=city)


@router.get("/demand/cities")
def get_cities():
    ml = MLService.get_instance()
    return ml.get_cities()


# ─── ANOMALY STATS ────────────────────────────────────────────────────────────

@router.get("/anomaly-stats")
def get_anomaly_stats(db: Session = Depends(get_db)):
    total = db.query(Review).count()
    flagged = db.query(Review).filter(Review.is_anomaly == True).count()
    avg_score = db.query(func.avg(Review.anomaly_score)).scalar()

    recent_anomalies = (
        db.query(Review)
        .filter(Review.is_anomaly == True)
        .order_by(Review.id.desc())
        .limit(20)
        .all()
    )

    return {
        "total_reviews": total,
        "flagged_anomalies": flagged,
        "flagged_pct": round(flagged / max(total, 1) * 100, 2),
        "avg_anomaly_score": round(float(avg_score or 0), 4),
        "recent_anomalies": [ReviewResponse.model_validate(r) for r in recent_anomalies],
    }


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@router.get("/dashboard-stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_musicians = db.query(Musician).count()
    total_bookings = db.query(Booking).count()
    total_events = db.query(Event).count()
    total_reviews = db.query(Review).count()
    avg_rating = db.query(func.avg(Booking.rating)).scalar() or 0
    avg_price = db.query(func.avg(Booking.price_charged)).scalar() or 0
    anomalies = db.query(Review).filter(Review.is_anomaly == True).count()

    return DashboardStats(
        total_musicians=total_musicians,
        total_clients=300,  # from seeded CSV
        total_bookings=total_bookings,
        total_events=total_events,
        total_reviews=total_reviews,
        avg_rating=round(float(avg_rating), 2),
        avg_price=round(float(avg_price), 2),
        anomaly_rate=round(anomalies / max(total_reviews, 1) * 100, 2),
    )
