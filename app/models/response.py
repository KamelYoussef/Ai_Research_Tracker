from sqlalchemy import Column, Integer, String
from app.database import Base

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    product = Column(String, index=True)
    location = Column(String, index=True)
    total_count = Column(Integer, default=0)
    ai_response = Column(String)

    # Optionally add a method to return a human-readable representation of the model
    def __repr__(self):
        return f"<Response(id={self.id}, product={self.product}, location={self.location}, total_count={self.total_count})>"
