"""
Review model — seeded from reviews.csv
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Text
from database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    review_id = Column(String, unique=True, nullable=False, index=True)
    booking_id = Column(String, nullable=False, index=True)
    review_text = Column(Text, nullable=True)
    rating = Column(Integer, default=0)
    created_at = Column(String, nullable=True)
    # Sentiment analysis results (populated by ML)
    sentiment_score = Column(Float, nullable=True)
    sentiment_label = Column(String, nullable=True)
    vader_score = Column(Float, nullable=True)
    bert_score = Column(Float, nullable=True)
    # Anomaly detection results
    is_anomaly = Column(Boolean, default=False)
    anomaly_score = Column(Float, nullable=True)
