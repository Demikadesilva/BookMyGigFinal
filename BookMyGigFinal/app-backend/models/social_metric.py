"""
Social Media Metric model — seeded from social_media_metrics.csv
"""
from sqlalchemy import Column, String, Integer
from database import Base


class SocialMetric(Base):
    __tablename__ = "social_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    musician_id = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=True)
    followers = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    views = Column(Integer, default=0)
    date_collected = Column(String, nullable=True)
