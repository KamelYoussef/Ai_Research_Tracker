from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.dependencies import get_db
from app.models.response import Response
from app.models.user import User
from datetime import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.utils.helpers import track_responses, get_ai_response, aggregate_total_by_product, \
    aggregate_total_by_location, aggregate_total_by_product_and_location, calculate_score_ai, create_access_token, \
    validate_token, verify_password, admin_required, hash_password


router = APIRouter()
security = HTTPBearer()


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
    prompt: str


class UserCreateRequest(BaseModel):
    username: str
    password: str
    role: str = "user"


@router.post("/submit_query_with_ai_platform")
async def submit_query_with_ai_platform(query: QueryRequest, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Handles a query request with default configurations.

    :param query: QueryRequest object containing ai_platform, locations, and products.
    :return: Processed AI responses and results.
    """
    current_date = datetime.now().strftime("%Y%m")
    current_day = datetime.now().strftime("%d")

    try:
        validate_token(credentials)
        # Call the tracking function with provided inputs
        ai_responses, results = track_responses(
            ai_platform=query.ai_platform,
            config_path="app/config.yml",
            locations=query.locations,
            products=query.products,
            prompt=query.prompt
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
async def aggregate_total_by_product_route(month: str, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Aggregate total_count by product for a given month.

    Args:
        month (str): Month in YYYYMM format.
        db (Session): SQLAlchemy session.

    Returns:
        List[dict]: Aggregated totals by product.
    """
    try:
        validate_token(credentials)
        # Call the helper function to aggregate data
        aggregated_data = aggregate_total_by_product(db=db, month=month)
        return {"aggregated_data": aggregated_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aggregating data: {str(e)}")


@router.get("/aggregate_total_by_location/{month}")
async def aggregate_total_by_location_route(month: str, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get the aggregated total_count by location for a given month.

    Args:
        month (str): Month in YYYYMM format.

    Returns:
        JSON: Aggregated totals by location.
    """
    try:
        validate_token(credentials)
        aggregated_data = aggregate_total_by_location(db, month)
        return {"aggregated_data": aggregated_data}
    except Exception as e:
        return {"error": str(e)}


@router.get("/aggregate_total_by_product_and_location/{month}")
async def aggregate_total_by_product_and_location_route(month: str, db: Session = Depends(get_db), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Endpoint to aggregate total_count by product and location for a given month.

    Args:
        month (str): Month in YYYYMM format.
        db (Session): SQLAlchemy session.

    Returns:
        dict: Aggregated totals by product and location.
    """
    try:
        validate_token(credentials)
        aggregated_data = aggregate_total_by_product_and_location(db, month)
        return {"aggregated_data": aggregated_data}
    except Exception as e:
        return {"error": str(e)}


@router.get("/score_ai/{month}/{flag_competitor}")
async def get_score_ai(
        month: str,
        flag_competitor: str,
        db: Session = Depends(get_db),
        credentials: HTTPAuthorizationCredentials = Depends(security)  # Token validation here
):
    """
    Calculate and return the AI score for a given month, with token validation.

    Args:
        month (str): Month in YYYYMM format.
        flag_competitor (str): Flag representing the competitor.
        db (Session): Database session dependency.

    Returns:
        dict: The month and corresponding AI score.
    """
    try:
        # Validate the token using the validate_token function
        validate_token(credentials)

        # If token is valid, calculate the AI score
        score = calculate_score_ai(db, month, "app/config.yml", flag_competitor)

        return {"month": month, "score_ai": int(score)}

    except HTTPException as e:
        raise e  # If token is invalid, HTTPException will be raised in validate_token()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating score: {str(e)}")


@router.post("/login", response_model=Token)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Query the user from the database
    user = db.query(User).filter(User.username == request.username).first()

    # Check if user exists and password is correct
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create the access token
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/validate_token")
async def validate_token_route(payload: dict = Depends(validate_token)):
    """
    Route to validate a token.
    """
    return {"message": "Token is valid", "payload": payload}


@router.post("/add_user")
def add_user(request: UserCreateRequest, db: Session = Depends(get_db),
             _: dict = Depends(admin_required)):
    """
        Add a new user to the database.
        Only accessible by users with the 'admin' role.
    """
    # Check if the user already exists
    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Create the new user
    new_user = User(username=request.username, password_hash=hash_password(request.password), role=request.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User created successfully", "user": new_user.username}


@router.delete("/delete_user")
def delete_user(username: str, db: Session = Depends(get_db), _: dict = Depends(admin_required)):
    """
    Delete a user from the database.
    Only accessible by users with the 'admin' role.
    """
    # Check if the user exists
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Delete the user
    db.delete(user)
    db.commit()

    return {"message": f"User '{username}' deleted successfully"}
