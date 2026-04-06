"""
Event model — seeded from events.csv
"""
from sqlalchemy import Column, String, Integer, Float, DateTime
from database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, nullable=False, index=True)
    client_id = Column(String, nullable=False, index=True)
    city = Column(String, nullable=True)
    date_time = Column(String, nullable=True)
    expected_pax = Column(Integer, default=0)
    event_type = Column(String, nullable=True)
    budget = Column(Float, default=0.0)
