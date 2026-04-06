"""
Events Router — CRUD for events.
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from database import get_db
from models.event import Event
from schemas import EventResponse, CreateEventRequest
from services.auth_service import get_current_user

router = APIRouter(prefix="/events", tags=["Events"])


def _get_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.get("")
def list_all_events(
    db: Session = Depends(get_db),
    limit: int = 50,
    city: str = None,
    event_type: str = None,
):
    q = db.query(Event)
    if city:
        q = q.filter(Event.city.ilike(f"%{city}%"))
    if event_type:
        q = q.filter(Event.event_type.ilike(f"%{event_type}%"))
    events = q.limit(limit).all()
    return [EventResponse.model_validate(e) for e in events]


@router.get("/me")
def my_events(authorization: str = Header(None), db: Session = Depends(get_db)):
    user = _get_user(authorization, db)
    client_id = user.client_id
    if not client_id:
        return []
    events = db.query(Event).filter(Event.client_id == client_id).all()
    return [EventResponse.model_validate(e) for e in events]


@router.post("", response_model=EventResponse, status_code=201)
def create_event(
    req: CreateEventRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    user = _get_user(authorization, db)
    client_id = user.client_id
    if not client_id:
        raise HTTPException(status_code=403, detail="Only clients can create events")

    count = db.query(Event).count()
    event_id = f"E{count + 1:03d}"

    event = Event(
        event_id=event_id,
        client_id=client_id,
        city=req.city,
        date_time=req.date_time,
        expected_pax=req.expected_pax,
        event_type=req.event_type,
        budget=req.budget,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
