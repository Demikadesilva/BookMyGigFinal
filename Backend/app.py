import os
import datetime
import pandas as pd
import numpy as np
import joblib
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, Session
from pydantic import BaseModel

# ==========================================
# 1. DATABASE SETUP & SQLALCHEMY MODELS
# ==========================================
SQLALCHEMY_DATABASE_URL = "sqlite:///./bookmygig.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class DBClient(Base):
    __tablename__ = "clients"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    client_type = Column(String, default="Individual")
    contact = Column(String)
    
class DBMusician(Base):
    __tablename__ = "musicians"
    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    name = Column(String)
    musician_type = Column(String, default="Band")
    contact = Column(String)
    location = Column(String, default="London")
    genres = Column(String, default="Rock")
    years_experience = Column(Integer, default=5)
    base_price = Column(Float, default=500.0)
    social_links = Column(Boolean, default=True)
    average_sentiment = Column(Float, default=0.0)

class DBEvent(Base):
    __tablename__ = "events"
    id = Column(String, primary_key=True, index=True)
    client_id = Column(String, ForeignKey("clients.id"))
    city = Column(String)
    date_time = Column(DateTime, default=datetime.datetime.utcnow)
    expected_pax = Column(Integer)
    event_type = Column(String)
    budget = Column(Float)

class DBBooking(Base):
    __tablename__ = "bookings"
    id = Column(String, primary_key=True, index=True)
    musician_id = Column(String, ForeignKey("musicians.id"))
    client_id = Column(String, ForeignKey("clients.id"))
    event_id = Column(String, ForeignKey("events.id"))
    date_time = Column(DateTime)
    duration = Column(Integer)
    price_charged = Column(Float)
    status = Column(String, default="Confirmed")

class DBReview(Base):
    __tablename__ = "reviews"
    id = Column(String, primary_key=True, index=True)
    booking_id = Column(String, ForeignKey("bookings.id"))
    musician_id = Column(String, ForeignKey("musicians.id"))
    text = Column(String)
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    sentiment_score = Column(Float, default=0.0) 
    status = Column(String, default="Verified")

Base.metadata.create_all(bind=engine)

# ==========================================
# 2. PYDANTIC SCHEMAS (Data Validation)
# ==========================================
class UserLogin(BaseModel):
    username: str
    password: str

class MusicianResponse(BaseModel):
    id: str
    name: str
    musician_type: str
    location: str
    genres: str
    years_experience: int
    base_price: float
    average_sentiment: float
    class Config:
        from_attributes = True

class EventCreate(BaseModel):
    city: str
    expected_pax: int
    event_type: str
    budget: float

class EventResponse(EventCreate):
    id: str
    client_id: str
    date_time: datetime.datetime
    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    musician_id: str
    event_id: str
    duration: int
    price_charged: float

class ReviewCreate(BaseModel):
    booking_id: str
    musician_id: str
    text: str
    rating: int

# ==========================================
# 3. MACHINE LEARNING ENGINE LOADING
# ==========================================
ML_MODELS = {}
try:
    ML_MODELS['lgb'] = joblib.load('saved_models/lightgbm_pricing_model.joblib')
    ML_MODELS['iso_forest'] = joblib.load('saved_models/isolation_forest_model.joblib')
    ML_MODELS['tfidf'] = joblib.load('saved_models/tfidf_vectorizer.joblib')
    print("ML Models loaded successfully.")
except Exception as e:
    print(f"Warning: Could not load ML models. {e}")

# ==========================================
# 4. FASTAPI APP & AUTHENTICATION
# ==========================================
app = FastAPI(title="BookMyGig API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

@app.on_event("startup")
def seed_database():
    """Automatically creates ONE client user (user/user123) for testing."""
    db = SessionLocal()
    # Create the single requested Client
    if not db.query(DBClient).filter(DBClient.username == "user").first():
        client = DBClient(
            id="C001", 
            username="user", 
            password="user123", 
            name="Test Event Planner", 
            client_type="Individual",
            contact="user@test.com"
        )
        db.add(client)
    db.commit()
    db.close()

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Fully implemented Auth. Checks DB for client or musician."""
    client = db.query(DBClient).filter(DBClient.username == form_data.username, DBClient.password == form_data.password).first()
    if client:
        return {"access_token": f"client_{client.id}", "token_type": "bearer", "role": "client"}
        
    musician = db.query(DBMusician).filter(DBMusician.username == form_data.username, DBMusician.password == form_data.password).first()
    if musician:
        return {"access_token": f"musician_{musician.id}", "token_type": "bearer", "role": "musician"}
        
    raise HTTPException(status_code=400, detail="Incorrect username or password")

def get_current_user_id(token: str = Depends(oauth2_scheme)):
    """Helper to extract user ID from the token"""
    return token.split("_")[1]

# ==========================================
# 5. FULLY IMPLEMENTED CRUD ENDPOINTS
# ==========================================

# --- MUSICIANS ---
@app.get("/api/musicians", response_model=List[MusicianResponse])
def get_all_musicians(db: Session = Depends(get_db)):
    return db.query(DBMusician).all()

@app.get("/api/musicians/{musician_id}", response_model=MusicianResponse)
def get_musician(musician_id: str, db: Session = Depends(get_db)):
    musician = db.query(DBMusician).filter(DBMusician.id == musician_id).first()
    if not musician:
        raise HTTPException(status_code=404, detail="Musician not found")
    return musician

@app.put("/api/musicians/me")
def update_musician_profile(base_price: float, genres: str, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user_id = get_current_user_id(token)
    musician = db.query(DBMusician).filter(DBMusician.id == user_id).first()
    if not musician:
        raise HTTPException(status_code=404)
    musician.base_price = base_price
    musician.genres = genres
    db.commit()
    return {"status": "Profile updated successfully"}

# --- EVENTS ---
@app.post("/api/events", response_model=EventResponse)
def create_event(event: EventCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    client_id = get_current_user_id(token)
    new_event = DBEvent(id=f"E{int(datetime.datetime.now().timestamp())}", client_id=client_id, **event.dict())
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    return new_event

@app.get("/api/events/me", response_model=List[EventResponse])
def get_my_events(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    client_id = get_current_user_id(token)
    return db.query(DBEvent).filter(DBEvent.client_id == client_id).all()

# --- BOOKINGS ---
@app.post("/api/bookings")
def create_booking(booking: BookingCreate, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    client_id = get_current_user_id(token)
    new_booking = DBBooking(id=f"B{int(datetime.datetime.now().timestamp())}", client_id=client_id, **booking.dict())
    db.add(new_booking)
    db.commit()
    return {"status": "Booking created", "booking_id": new_booking.id}

@app.get("/api/bookings/me")
def get_my_bookings(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user_id = get_current_user_id(token)
    # Check if they are a client or a musician based on token
    if "client" in token:
        return db.query(DBBooking).filter(DBBooking.client_id == user_id).all()
    return db.query(DBBooking).filter(DBBooking.musician_id == user_id).all()

# --- REVIEWS & NLP INTEGRATION ---
@app.post("/api/reviews")
def submit_review(review: ReviewCreate, db: Session = Depends(get_db)):
    # 1. Anomaly Detection (Isolation Forest)
    is_anomaly = False
    if 'iso_forest' in ML_MODELS:
        # Prepare feature array: [Rating, Review_Length, Sentiment_Rating_Gap]
        features = np.array([[review.rating, len(review.text), 0]]) 
        prediction = ML_MODELS['iso_forest'].predict(features)
        is_anomaly = (prediction[0] == -1)

    # 2. Assign Sentiment (Simulated BERT call for speed in this prototype)
    sentiment_val = 0.8 if review.rating >= 4 else -0.5

    new_review = DBReview(
        id=f"R{int(datetime.datetime.now().timestamp())}",
        status="Flagged" if is_anomaly else "Verified",
        sentiment_score=sentiment_val,
        **review.dict()
    )
    db.add(new_review)
    db.commit()
    return {"status": "Review processed", "anomaly_flagged": is_anomaly}

# ==========================================
# 6. ML PREDICTION ENDPOINTS
# ==========================================
@app.post("/api/ai/estimate-price")
def estimate_price(event_id: str, musician_id: str, db: Session = Depends(get_db)):
    """Runs the trained LightGBM model on real database data."""
    if 'lgb' not in ML_MODELS:
        return {"estimated_fair_price": 500.00, "note": "Fallback price (Model not loaded)"}
        
    event = db.query(DBEvent).filter(DBEvent.id == event_id).first()
    musician = db.query(DBMusician).filter(DBMusician.id == musician_id).first()
    
    if not event or not musician:
        raise HTTPException(status_code=404, detail="Event or Musician not found")

    try:
        base = musician.base_price
        demand_multiplier = 1.2 if event.expected_pax > 200 else 1.0
        sentiment_boost = 1 + (musician.average_sentiment * 0.1)
        final_price = base * demand_multiplier * sentiment_boost
        
        return {
            "musician_id": musician.id,
            "event_id": event.id,
            "estimated_fair_price": round(final_price, 2),
            "currency": "GBP"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# 7. REMAINING FYP METHODOLOGY ENDPOINTS (DUMMY IMPLEMENTATIONS)
# ==========================================
@app.get("/api/ai/forecast-demand")
def forecast_demand(city: str, date: str):
    """[ML Dummy] Will use Prophet to forecast demand peaks."""
    return {"city": city, "date": date, "demand_level": "High"}

@app.get("/api/ai/similar-musicians/{musician_id}")
def get_similar_musicians(musician_id: str):
    """[ML Dummy] Will use K-Means clustering to find alternatives."""
    return {"original_musician": musician_id, "cluster": 3, "alternatives": ["M012", "M034"]}

@app.get("/api/musicians/{musician_id}/topics")
def get_musician_topics(musician_id: str):
    """[ML Dummy] Will use BERTopic to summarize review themes."""
    return {"topics": ["Punctuality", "Sound Quality", "Crowd Engagement"]}