"""
BookMyGig — Application Configuration
"""
from pathlib import Path
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
ML_MODELS_DIR = PROJECT_ROOT / "New V1" / "saved_models"
RAW_DATA_DIR = PROJECT_ROOT / "New V1" / "data" / "raw"
DATABASE_PATH = BASE_DIR / "bookmygig.db"

# ── JWT ───────────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "bookmygig-super-secret-key-change-in-prod-2025")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# ── CORS ──────────────────────────────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ── Model Paths ───────────────────────────────────────────────────────────────
PRICING_MODEL_PATH = ML_MODELS_DIR / "pricing"
ANOMALY_MODEL_PATH = ML_MODELS_DIR / "anomaly"
RECOMMENDATION_MODEL_PATH = ML_MODELS_DIR / "recommendation"
DEMAND_MODEL_PATH = ML_MODELS_DIR / "demand"
SENTIMENT_MODEL_PATH = ML_MODELS_DIR / "sentiment"
DISTILBERT_MODEL_PATH = ML_MODELS_DIR / "distilbert_finetuned"
