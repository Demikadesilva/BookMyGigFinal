"""
Booking model — seeded from bookings.csv
"""
from sqlalchemy import Column, String, Integer, Float
from database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    booking_id = Column(String, unique=True, nullable=False, index=True)
    musician_id = Column(String, nullable=False, index=True)
    client_id = Column(String, nullable=False, index=True)
    event_id = Column(String, nullable=False, index=True)
    date_time = Column(String, nullable=True)
    duration = Column(Integer, default=1)
    price_charged = Column(Float, default=0.0)
    rating = Column(Integer, default=0)
