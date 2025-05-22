from sqlalchemy import Column, Integer, String, JSON, Index
from app.database import Base


class Sources(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    ai_platform = Column(String, index=True)
    date = Column(String(6), index=True)
    day = Column(String(2), index=True)
    sources = Column(JSON)

