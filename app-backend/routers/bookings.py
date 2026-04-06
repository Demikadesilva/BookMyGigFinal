"""
Bookings Router — Create and list bookings.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from database import get_db
from models.booking import Booking
from models.musician import Musician
from models.event import Event
from schemas import BookingResponse, CreateBookingRequest
from services.auth_service import get_current_user

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def _get_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("")
def list_bookings(db: Session = Depends(get_db), limit: int = 50):
    bookings = db.query(Booking).limit(limit).all()
    return _enrich(bookings, db)


@router.get("/me")
def my_bookings(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _get_user(authorization, db)
    client_id = user.client_id
    musician_id = user.musician_id

    if client_id:
        bookings = db.query(Booking).filter(Booking.client_id == client_id).all()
    elif musician_id:
        bookings = db.query(Booking).filter(Booking.musician_id == musician_id).all()
    else:
        return []

    return _enrich(bookings, db)


@router.post("", status_code=201)
def create_booking(
    req: CreateBookingRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    user = _get_user(authorization, db)
    if not user.client_id:
        raise HTTPException(status_code=403, detail="Only clients can create bookings")

    count = db.query(Booking).count()
    booking_id = f"B{count + 1:03d}"

    booking = Booking(
        booking_id=booking_id,
        musician_id=req.musician_id,
        client_id=user.client_id,
        event_id=req.event_id,
        duration=req.duration,
        price_charged=req.price_charged,
        rating=0,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return {"booking_id": booking.booking_id, "status": "created"}


def _enrich(bookings, db):
    """Add musician name, event type, city to booking responses."""
    results = []
    for b in bookings:
        musician = db.query(Musician).filter(Musician.musician_id == b.musician_id).first()
        event = db.query(Event).filter(Event.event_id == b.event_id).first()
        results.append(BookingResponse(
            booking_id=b.booking_id,
            musician_id=b.musician_id,
            client_id=b.client_id,
            event_id=b.event_id,
            date_time=b.date_time,
            duration=b.duration,
            price_charged=b.price_charged,
            rating=b.rating,
            musician_name=musician.name if musician else None,
            event_type=event.event_type if event else None,
            city=event.city if event else None,
        ))
    return results
