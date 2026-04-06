"""
User model — handles authentication for both clients and musicians.
"""
from sqlalchemy import Column, String, Integer, DateTime, func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="client")  # "client" or "musician"
    client_id = Column(String, nullable=True)    # links to CSV Client_ID
    musician_id = Column(String, nullable=True)  # links to CSV Musician_ID
    created_at = Column(DateTime, server_default=func.now())
