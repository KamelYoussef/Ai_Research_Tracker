from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base


class Response(Base):
    __tablename__ = "ai_responses"

    id = Column(Integer, primary_key=True, index=True)
    product = Column(String, index=True)
    location = Column(String, index=True)
    is_city = Column(Boolean) #ALTER TABLE ai_responses ADD COLUMN is_city BOOLEAN;
    total_count = Column(Integer)
    ai_platform = Column(String, index=True)
    date = Column(String(6), index=True)
    day = Column(String(2), index=True)
    competitor_1 = Column(Integer)
    competitor_2 = Column(Integer)
    competitor_3 = Column(Integer)
    competitor_4 = Column(Integer) #ALTER TABLE ai_responses ADD COLUMN competitor_4 INTEGER;
    rank = Column(Integer)
    sentiment = Column(Float)
