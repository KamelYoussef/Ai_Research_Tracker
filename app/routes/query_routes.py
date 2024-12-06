from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
#from app.nlp.extractor import find_words_in_texts  # Make sure your helper function is imported
from app.services.storage import store_response
from app.dependencies import get_db
from app.models.response import Response
from app.services.ai_api import get_ai_response
from app.utils.helpers import track_responses
from app.utils.helpers import load_config, find_words_in_texts


router = APIRouter()


@router.post("/submit_query_with_default/")
async def submit_query_with_default(db: Session = Depends(get_db)):
    ai_responses, results = track_responses()
    # Store the response and AI response in the database
    for result, ai_response in zip(results, ai_responses):
        product = result.get('product')  # Assuming the result contains 'product'
        location = result.get('location')  # Assuming the result contains 'location'
        total_count = result.get('total_count')  # Assuming the result contains 'total_count'

        # Store the query and AI response in the database
        store_response(
            db=db,
            product=product,
            location=location,
            total_count=total_count,
            query="Your AI query here",  # Replace with the actual query if needed
            response_text=ai_response  # The corresponding AI response
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






