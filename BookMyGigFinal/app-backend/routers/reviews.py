"""
Reviews Router — Submit reviews (triggers sentiment + anomaly analysis).
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.review import Review
from models.booking import Booking
from schemas import ReviewResponse, CreateReviewRequest
from services.auth_service import get_current_user
from services.ml_service import MLService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


def _get_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("")
def list_reviews(db: Session = Depends(get_db), limit: int = 50):
    reviews = db.query(Review).limit(limit).all()
    return [ReviewResponse.model_validate(r) for r in reviews]


@router.post("", response_model=ReviewResponse, status_code=201)
def create_review(
    req: CreateReviewRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    user = _get_user(authorization, db)
    ml = MLService.get_instance()

    # Verify booking exists
    booking = db.query(Booking).filter(Booking.booking_id == req.booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Run sentiment analysis
    sentiment = ml.analyze_sentiment(req.review_text)

    # Get average musician rating for anomaly detection
    avg_rating = db.query(func.avg(Booking.rating)).filter(
        Booking.musician_id == booking.musician_id
    ).scalar() or 3.5

    # Run anomaly detection
    anomaly = ml.detect_anomaly(
        rating=req.rating,
        review_text=req.review_text,
        sentiment_score=sentiment["sentiment_score"],
        avg_musician_rating=float(avg_rating),
    )

    # Create review
    count = db.query(Review).count()
    review_id = f"R{count + 1:03d}"

    review = Review(
        review_id=review_id,
        booking_id=req.booking_id,
        review_text=req.review_text,
        rating=req.rating,
        sentiment_score=sentiment["sentiment_score"],
        sentiment_label=sentiment["sentiment_label"],
        vader_score=sentiment["vader_score"],
        bert_score=sentiment.get("bert_score"),
        is_anomaly=anomaly["is_anomaly"],
        anomaly_score=anomaly["anomaly_score"],
    )
    db.add(review)

    # Update booking rating
    booking.rating = req.rating
    db.commit()
    db.refresh(review)

    return review
