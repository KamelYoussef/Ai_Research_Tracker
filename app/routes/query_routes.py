from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from sqlalchemy.orm import Session
from app.services.storage import store_response
from app.dependencies import get_db
from app.models.response import Response
from sqlalchemy import func
from app.utils.helpers import track_responses, get_ai_response, aggregate_total_by_product, aggregate_total_by_location


router = APIRouter()


@router.post("/submit_query_with_default/")
async def submit_query_with_default(ai_platform, db: Session = Depends(get_db)):
    current_date = datetime.now().strftime("%Y%m")
    ai_responses, results = track_responses(ai_platform)
    # Store the response and AI response in the database
    for result, ai_response in zip(results, ai_responses):
        product = result.get('product')
        location = result.get('location')
        total_count = result.get('total_count')

        # Store the query and AI response in the database
        store_response(
            db=db,
            product=product,
            location=location,
            total_count=total_count,
            ai_platform="ai_platform",
            date=current_date
        )

    return {"message": "Query submitted successfully", "search_results": results, "ai_response": ai_responses}


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
async def get_total_by_location(month: str, db: Session = Depends(get_db)):
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
def aggregate_data(month: str, db: Session = Depends(get_db)):
    """
    Endpoint to aggregate total_count by product and location for a given month.

    Args:
        month (str): Month in YYYYMM format.
        db (Session): SQLAlchemy session.

    Returns:
        dict: Aggregated totals by product and location.
    """
    results = (
        db.query(
            Response.product,
            Response.location,
            func.sum(Response.total_count).label("total_count"),
            Response.day,
        )
        .filter(Response.date == month)
        .group_by(Response.product, Response.location, Response.day,)
        .all()
    )
    return {"aggregated_data":
                [
                    {"product": r[0],
                     "location": r[1],
                     "total_count": r[2],
                     "day": r[3]
                     }
                    for r in results
                ]
            }

