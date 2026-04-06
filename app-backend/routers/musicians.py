"""
Musicians Router — Browse, filter, and get musician details.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.musician import Musician
from models.booking import Booking
from models.review import Review
from models.social_metric import SocialMetric
from schemas import MusicianResponse, MusicianListResponse

router = APIRouter(prefix="/musicians", tags=["Musicians"])


@router.get("", response_model=MusicianListResponse)
def list_musicians(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    genre: str = Query(None),
    location: str = Query(None),
    musician_type: str = Query(None),
    search: str = Query(None),
    min_price: float = Query(None),
    max_price: float = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Musician)

    if genre:
        q = q.filter(Musician.genres.ilike(f"%{genre}%"))
    if location:
        q = q.filter(Musician.location.ilike(f"%{location}%"))
    if musician_type:
        q = q.filter(Musician.musician_type.ilike(f"%{musician_type}%"))
    if search:
        q = q.filter(Musician.name.ilike(f"%{search}%"))
    if min_price is not None:
        q = q.filter(Musician.base_price >= min_price)
    if max_price is not None:
        q = q.filter(Musician.base_price <= max_price)

    total = q.count()
    musicians = q.offset((page - 1) * page_size).limit(page_size).all()

    results = []
    for m in musicians:
        # Get aggregated stats
        avg_rating = db.query(func.avg(Booking.rating)).filter(
            Booking.musician_id == m.musician_id
        ).scalar()
        booking_count = db.query(func.count(Booking.id)).filter(
            Booking.musician_id == m.musician_id
        ).scalar()
        total_followers = db.query(func.sum(SocialMetric.followers)).filter(
            SocialMetric.musician_id == m.musician_id
        ).scalar()

        results.append(MusicianResponse(
            musician_id=m.musician_id,
            name=m.name,
            musician_type=m.musician_type,
            contact=m.contact,
            location=m.location,
            genres=m.genres,
            years_experience=m.years_experience,
            base_price=m.base_price,
            has_social_links=m.has_social_links,
            avg_rating=round(avg_rating, 2) if avg_rating else None,
            booking_count=booking_count or 0,
            total_followers=total_followers or 0,
        ))

    return MusicianListResponse(
        musicians=results, total=total, page=page, page_size=page_size
    )


@router.get("/filters")
def get_filters(db: Session = Depends(get_db)):
    """Get available filter options."""
    genres = set()
    for m in db.query(Musician.genres).distinct().all():
        if m.genres:
            genres.add(m.genres)
    locations = [r[0] for r in db.query(Musician.location).distinct().all() if r[0]]
    types = [r[0] for r in db.query(Musician.musician_type).distinct().all() if r[0]]
    return {
        "genres": sorted(genres),
        "locations": sorted(locations),
        "types": sorted(types),
    }


@router.get("/{musician_id}", response_model=MusicianResponse)
def get_musician(musician_id: str, db: Session = Depends(get_db)):
    m = db.query(Musician).filter(Musician.musician_id == musician_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Musician not found")

    avg_rating = db.query(func.avg(Booking.rating)).filter(
        Booking.musician_id == musician_id
    ).scalar()
    booking_count = db.query(func.count(Booking.id)).filter(
        Booking.musician_id == musician_id
    ).scalar()
    total_followers = db.query(func.sum(SocialMetric.followers)).filter(
        SocialMetric.musician_id == musician_id
    ).scalar()

    return MusicianResponse(
        musician_id=m.musician_id,
        name=m.name,
        musician_type=m.musician_type,
        contact=m.contact,
        location=m.location,
        genres=m.genres,
        years_experience=m.years_experience,
        base_price=m.base_price,
        has_social_links=m.has_social_links,
        avg_rating=round(avg_rating, 2) if avg_rating else None,
        booking_count=booking_count or 0,
        total_followers=total_followers or 0,
    )


@router.get("/{musician_id}/reviews")
def get_musician_reviews(musician_id: str, db: Session = Depends(get_db)):
    """Get all reviews for a musician (via bookings)."""
    bookings = db.query(Booking).filter(Booking.musician_id == musician_id).all()
    booking_ids = [b.booking_id for b in bookings]

    if not booking_ids:
        return []

    reviews = db.query(Review).filter(Review.booking_id.in_(booking_ids)).all()
    return [
        {
            "review_id": r.review_id,
            "booking_id": r.booking_id,
            "review_text": r.review_text,
            "rating": r.rating,
            "created_at": r.created_at,
            "sentiment_score": r.sentiment_score,
            "sentiment_label": r.sentiment_label,
            "vader_score": r.vader_score,
            "bert_score": r.bert_score,
            "is_anomaly": r.is_anomaly,
            "anomaly_score": r.anomaly_score,
        }
        for r in reviews
    ]
