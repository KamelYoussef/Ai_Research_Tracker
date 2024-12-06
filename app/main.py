from fastapi import FastAPI
from app.database import Base, engine
from app.routes.query_routes import router as query_router
from app.models.response import Response

app = FastAPI()

# Include the query routes
app.include_router(query_router)

# Create the database tables if they don't exist
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)



