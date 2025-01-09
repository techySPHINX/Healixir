from sqlalchemy import Column, Integer, String, Boolean, Float, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firebase_uid = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    role = Column(String, default="outsider")  # Add role field with default
    is_active = Column(Boolean, default=True)

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    distance = Column(Float)  # Distance from a reference point (optional)
    rating = Column(Float, nullable=True)  # Average rating (e.g., 4.5 out of 5)
    reviews = Column(Text, nullable=True)  # JSON string of reviews or a text blob

