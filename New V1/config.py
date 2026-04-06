"""
Central configuration for the BookMyGig AI pipeline.
All paths, hyperparameters, and settings live here.
"""

import os
from pathlib import Path

# ── Project Root ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent

# ── Data Paths ────────────────────────────────────────────────────────────────
DATA_DIR        = ROOT / "data"
RAW_DIR         = DATA_DIR / "raw"
PROCESSED_DIR   = DATA_DIR / "processed"
GENERATION_DIR  = DATA_DIR / "generation"

# ── Model Paths ───────────────────────────────────────────────────────────────
SAVED_MODELS_DIR = ROOT / "saved_models"
SAVED_MODELS_DIR.mkdir(exist_ok=True)

# ── CSV file names ────────────────────────────────────────────────────────────
MUSICIANS_CSV       = RAW_DIR / "musicians.csv"
CLIENTS_CSV         = RAW_DIR / "clients.csv"
EVENTS_CSV          = RAW_DIR / "events.csv"
BOOKINGS_CSV        = RAW_DIR / "bookings.csv"
REVIEWS_CSV         = RAW_DIR / "reviews.csv"
SOCIAL_METRICS_CSV  = RAW_DIR / "social_media_metrics.csv"

# Processed
PROCESSED_MUSICIANS_CSV = PROCESSED_DIR / "musicians_processed.csv"
PROCESSED_REVIEWS_CSV   = PROCESSED_DIR / "reviews_processed.csv"
PROCESSED_BOOKINGS_CSV  = PROCESSED_DIR / "bookings_processed.csv"
MASTER_CSV              = PROCESSED_DIR / "master_dataset.csv"

# ── Random Seed ───────────────────────────────────────────────────────────────
RANDOM_SEED = 42

# ── Sentiment Model ───────────────────────────────────────────────────────────
VADER_THRESHOLD_POS  = 0.05
VADER_THRESHOLD_NEG  = -0.05
DISTILBERT_MODEL     = "distilbert-base-uncased-finetuned-sst-2-english"
DISTILBERT_MAX_LEN   = 256
SENTIMENT_WEIGHT_VADER  = 0.4   # blending weight
SENTIMENT_WEIGHT_BERT   = 0.6

# ── Anomaly Detection ─────────────────────────────────────────────────────────
ISOLATION_FOREST_CONTAMINATION = 0.08   # 8% expected anomaly rate
ISOLATION_FOREST_ESTIMATORS    = 200
ANOMALY_FEATURES = [
    "Rating", "Review_Length", "Sentiment_Score",
    "Sentiment_Rating_Gap", "Avg_Musician_Rating",
]

# ── Recommendation System ─────────────────────────────────────────────────────
SVD_COMPONENTS    = 25
HYBRID_ALPHA_MIN  = 0.0   # pure CBF (cold start)
HYBRID_ALPHA_MAX  = 0.7   # mostly CF (warm users)
HYBRID_BETA       = 0.2   # sentiment boost weight
TOP_N_RECS        = 10
TFIDF_MAX_FEATURES = 5000

# ── Dynamic Pricing ───────────────────────────────────────────────────────────
PRICING_FEATURES = [
    "Expected_Pax", "Duration", "Years_Experience",
    "Base_Price", "Avg_Sentiment_Score", "Booking_Count",
    "Event_Type_enc", "City_enc", "Musician_Type_enc",
    "Followers_total", "Views_total",
]
LGBM_PARAMS = {
    "n_estimators":    500,
    "learning_rate":   0.03,
    "max_depth":       6,
    "num_leaves":      50,
    "min_child_samples": 10,
    "subsample":       0.8,
    "colsample_bytree": 0.8,
    "reg_alpha":       0.1,
    "reg_lambda":      0.1,
    "random_state":    RANDOM_SEED,
    "n_jobs":          -1,
    "verbose":         -1,
}
TEST_SIZE   = 0.2
VAL_SIZE    = 0.1

# ── Demand Forecasting ────────────────────────────────────────────────────────
DEMAND_LAG_WEEKS   = [1, 2, 4, 8]
DEMAND_ROLL_WINDOWS = [4, 8, 12]

# ── Azure OpenAI (LLM Judge) ──────────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT    = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY     = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
AZURE_OPENAI_DEPLOYMENT  = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-chat")

# ── Evaluation ────────────────────────────────────────────────────────────────
EVAL_REPORT_DIR = ROOT / "evaluation" / "reports"
EVAL_REPORT_DIR.mkdir(parents=True, exist_ok=True)
