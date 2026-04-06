"""
BookMyGig — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import FRONTEND_URL
from database import engine, Base

# Import all models to register them with SQLAlchemy
from models import User, Musician, Event, Booking, Review, SocialMetric

from routers import auth, musicians, events, bookings, reviews, ai


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables and seed database."""
    print("=" * 60)
    print("  BookMyGig API — Starting Up")
    print("=" * 60)

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("[DB] Tables created ✓")

    # Seed database from CSVs
    from seed import seed_database
    seed_database()

    print("[APP] Ready to serve requests!")
    print("=" * 60)
    yield
    print("[APP] Shutting down...")


app = FastAPI(
    title="BookMyGig API",
    description="AI-Powered UK Music Booking Platform — 5 ML Models Integrated",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(musicians.router)
app.include_router(events.router)
app.include_router(bookings.router)
app.include_router(reviews.router)
app.include_router(ai.router)


@app.get("/")
def root():
    return {
        "name": "BookMyGig API",
        "version": "2.0.0",
        "status": "running",
        "models": [
            "Dynamic Pricing (LightGBM)",
            "Sentiment Analysis (VADER + DistilBERT)",
            "Anomaly Detection (Isolation Forest)",
            "Hybrid Recommendation (CBF + CF + SVD)",
            "Demand Forecasting (LightGBM Time-Series)",
        ],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
