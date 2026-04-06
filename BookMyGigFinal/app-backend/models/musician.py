"""
Musician model — seeded from musicians.csv
"""
from sqlalchemy import Column, String, Integer, Float, Boolean
from database import Base


class Musician(Base):
    __tablename__ = "musicians"

    id = Column(Integer, primary_key=True, autoincrement=True)
    musician_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    musician_type = Column(String, nullable=False)
    contact = Column(String, nullable=True)
    location = Column(String, nullable=True)
    genres = Column(String, nullable=True)
    years_experience = Column(Integer, default=0)
    base_price = Column(Float, default=0.0)
    has_social_links = Column(Boolean, default=False)
