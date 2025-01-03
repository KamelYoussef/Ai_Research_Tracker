from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.dependencies import get_db
from app.models.response import Response
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from app.utils.helpers import track_responses, get_ai_response, aggregate_total_by_product, \
    aggregate_total_by_location, aggregate_total_by_product_and_location, calculate_score_ai, create_access_token, verify_token


router = APIRouter()

# OAuth2 scheme for extracting tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class QueryRequest(BaseModel):
    ai_platform: str
    locations: list[str]
    products: list[str]


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Extract and verify the current user from the token.
    """
    return verify_token(token)


@router.post("/submit_query_with_ai_platform")
async def submit_query_with_ai_platform(query: QueryRequest):
    """
    Handles a query request with default configurations.

    :param query: QueryRequest object containing ai_platform, locations, and products.
    :return: Processed AI responses and results.
    """
    current_date = datetime.now().strftime("%Y%m")
    current_day = datetime.now().strftime("%d")

    try:
        # Call the tracking function with provided inputs
        ai_responses, results = track_responses(
            ai_platform=query.ai_platform,
            config_path="app/config.yml",
            locations=query.locations,
            products=query.products
        )

        return {
            "ai_platform": query.ai_platform,
            "ai_responses": ai_responses,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")



@router.get("/responses/")
async def fetch_responses(db: Session = Depends(get_db)):
    """
    Fetch all saved AI responses from the database.
    """
    responses = db.query(Response).all()
    return {"responses": responses}


@router.post("/submit_query/")
async def submit_query(prompt, ai_platform):
    ai_response = get_ai_response(prompt, ai_platform=ai_platform)

    return {"message": "Query submitted successfully", "response": ai_response}


@router.get("/aggregate_total_by_product/{month}")
async def aggregate_total_by_product_route(month: str, db: Session = Depends(get_db)):
    """
    Aggregate total_count by product for a given month.

    Args:
        month (str): Month in YYYYMM format.
        db (Session): SQLAlchemy session.

    Returns:
        List[dict]: Aggregated totals by product.
    """
    try:
        # Call the helper function to aggregate data
        aggregated_data = aggregate_total_by_product(db=db, month=month)
        return {"aggregated_data": aggregated_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aggregating data: {str(e)}")


@router.get("/aggregate_total_by_location/{month}")
async def aggregate_total_by_location_route(month: str, db: Session = Depends(get_db)):
    """
    Get the aggregated total_count by location for a given month.

    Args:
        month (str): Month in YYYYMM format.

    Returns:
        JSON: Aggregated totals by location.
    """
    try:
        aggregated_data = aggregate_total_by_location(db, month)
        return {"aggregated_data": aggregated_data}
    except Exception as e:
        return {"error": str(e)}


@router.get("/aggregate_total_by_product_and_location/{month}")
async def aggregate_total_by_product_and_location_route(month: str, db: Session = Depends(get_db)):
    """
    Endpoint to aggregate total_count by product and location for a given month.

    Args:
        month (str): Month in YYYYMM format.
        db (Session): SQLAlchemy session.

    Returns:
        dict: Aggregated totals by product and location.
    """
    try:
        aggregated_data = aggregate_total_by_product_and_location(db, month)
        return {"aggregated_data": aggregated_data}
    except Exception as e:
        return {"error": str(e)}


@router.get("/score_ai/{month}")
async def get_score_ai(month: str, db: Session = Depends(get_db)):
    """
    Calculate and return the AI score for a given month.

    Args:
        month (str): Month in YYYYMM format.

    Returns:
        float: AI score for the specified month.
    """
    try:
        score = calculate_score_ai(db, month, "app/config.yml")
        return {"month": month, "score_ai": int(score)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating score: {str(e)}")


@router.post("/login", response_model=Token)
def login(request: LoginRequest):
    # Replace this with your database logic
    if request.username != "testuser" or request.password != "testpass":
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": request.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/protected-route")
def protected_route(authorization: str = Header(None)):
    """
    A protected POST route that requires the token in the Authorization header (no 'Bearer').
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    # Validate the token
    try:
        current_user = verify_token(authorization)  # Directly use the token from the header
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return {"message": f"Hello, {current_user}! You have access to this protected route."}
