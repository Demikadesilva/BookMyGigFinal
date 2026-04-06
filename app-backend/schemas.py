"""
Pydantic schemas — request & response models for the API.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# Auth
# ═══════════════════════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "client"  # "client" or "musician"

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    client_id: Optional[str] = None
    musician_id: Optional[str] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════════════════════════════════════════
# Musician
# ═══════════════════════════════════════════════════════════════════════════════

class MusicianResponse(BaseModel):
    musician_id: str
    name: str
    musician_type: str
    contact: Optional[str] = None
    location: Optional[str] = None
    genres: Optional[str] = None
    years_experience: int = 0
    base_price: float = 0.0
    has_social_links: bool = False
    # Computed fields
    avg_rating: Optional[float] = None
    booking_count: Optional[int] = None
    total_followers: Optional[int] = None

    class Config:
        from_attributes = True

class MusicianListResponse(BaseModel):
    musicians: List[MusicianResponse]
    total: int
    page: int
    page_size: int


# ═══════════════════════════════════════════════════════════════════════════════
# Event
# ═══════════════════════════════════════════════════════════════════════════════

class EventResponse(BaseModel):
    event_id: str
    client_id: str
    city: Optional[str] = None
    date_time: Optional[str] = None
    expected_pax: int = 0
    event_type: Optional[str] = None
    budget: float = 0.0

    class Config:
        from_attributes = True

class CreateEventRequest(BaseModel):
    city: str
    date_time: str
    expected_pax: int
    event_type: str
    budget: float


# ═══════════════════════════════════════════════════════════════════════════════
# Booking
# ═══════════════════════════════════════════════════════════════════════════════

class BookingResponse(BaseModel):
    booking_id: str
    musician_id: str
    client_id: str
    event_id: str
    date_time: Optional[str] = None
    duration: int = 1
    price_charged: float = 0.0
    rating: int = 0
    # Joined fields
    musician_name: Optional[str] = None
    event_type: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True

class CreateBookingRequest(BaseModel):
    musician_id: str
    event_id: str
    duration: int
    price_charged: float


# ═══════════════════════════════════════════════════════════════════════════════
# Review
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewResponse(BaseModel):
    review_id: str
    booking_id: str
    review_text: Optional[str] = None
    rating: int = 0
    created_at: Optional[str] = None
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    vader_score: Optional[float] = None
    bert_score: Optional[float] = None
    is_anomaly: bool = False
    anomaly_score: Optional[float] = None

    class Config:
        from_attributes = True

class CreateReviewRequest(BaseModel):
    booking_id: str
    review_text: str
    rating: int


# ═══════════════════════════════════════════════════════════════════════════════
# AI
# ═══════════════════════════════════════════════════════════════════════════════

class PriceEstimateRequest(BaseModel):
    event_type: str
    city: str
    musician_type: str
    expected_pax: int
    duration: int
    years_experience: int
    base_price: float

class PriceEstimateResponse(BaseModel):
    estimated_price: float
    model_used: str
    features_used: dict

class SentimentRequest(BaseModel):
    text: str

class SentimentResponse(BaseModel):
    text: str
    vader_score: float
    bert_score: Optional[float] = None
    sentiment_score: float
    sentiment_label: str

class RecommendationResponse(BaseModel):
    musician_id: str
    musician_name: Optional[str] = None
    musician_type: Optional[str] = None
    genres: Optional[str] = None
    location: Optional[str] = None
    base_price: Optional[float] = None
    final_score: float
    cbf_score: float
    cf_score: float
    sentiment_boost: float

class DemandForecastResponse(BaseModel):
    week: str
    demand: float
    avg_price: Optional[float] = None
    avg_rating: Optional[float] = None

class AnomalyStatsResponse(BaseModel):
    total_reviews: int
    flagged_anomalies: int
    flagged_pct: float
    avg_anomaly_score: float
    recent_anomalies: List[ReviewResponse]

class DashboardStats(BaseModel):
    total_musicians: int
    total_clients: int
    total_bookings: int
    total_events: int
    total_reviews: int
    avg_rating: float
    avg_price: float
    anomaly_rate: float


# Resolve forward references
TokenResponse.model_rebuild()
