from fastapi import FastAPI
from app.database import Base, engine
from app.routes.query_routes import router as query_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the query routes
app.include_router(query_router)

# Create the database tables if they don't exist
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)



