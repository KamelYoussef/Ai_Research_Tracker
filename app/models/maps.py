from sqlalchemy import Column, String, Float, Integer, Boolean
from app.database import Base

class Maps(Base):
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True, index=True)
    location = Column(String, nullable=False)
    product = Column(String, nullable=False)
    date = Column(String(6), index=True)
    day = Column(String(2), index=True)
    rank = Column(Integer)
    rating = Column(Float)
    reviews = Column(Integer)
    is_city = Column(Boolean)
