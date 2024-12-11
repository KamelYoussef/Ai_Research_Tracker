from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.storage import store_response
from app.dependencies import get_db
from app.models.response import Response
from app.utils.helpers import track_responses, get_ai_response, aggregate_total_by_product, \
    aggregate_total_by_location, aggregate_total_by_product_and_location, calculate_score_ai


router = APIRouter()


@router.get("/submit_query_with_default/{ai_platform}")
async def submit_query_with_default(ai_platform: str):
    current_date = datetime.now().strftime("%Y%m")
    current_day = datetime.now().strftime("%d")

    try:
        # Call the tracking function
        ai_responses, results = track_responses(ai_platform, "app/config.yml")

        # Ensure the number of AI responses matches the number of results
        if len(ai_responses) != len(results):
            raise ValueError("Mismatch between AI responses and results")

        # Combine AI responses with corresponding results
        combined_data = []
        for ai_response, result in zip(ai_responses, results):
            product = result.get('product')
            location = result.get('location')
            total_count = result.get('total_count')

            combined_data.append({
                "product": product,
                "location": location,
                "total_count": total_count,
                "ai_response": ai_response,
                "ai_platform": ai_platform,
            })

        return {
            "status": "success",
            "platform": ai_platform,
            "data": combined_data
        }
    except Exception as e:
        # Handle errors gracefully and return a meaningful message
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


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

    return {"message": "Query submitted successfully", "response": ai_response.content}


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
def aggregate_total_by_product_and_location_route(month: str, db: Session = Depends(get_db)):
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
