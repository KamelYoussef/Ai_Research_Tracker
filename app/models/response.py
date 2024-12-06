from sqlalchemy import Column, Integer, String
from app.database import Base

class Response(Base):
    __tablename__ = "ai_responses"

    id = Column(Integer, primary_key=True, index=True)
    product = Column(String, index=True)
    location = Column(String, index=True)
    total_count = Column(Integer)
    query = Column(String)  # Store the query made to AI
    response_text = Column(String)  # Store the AI-generated response
