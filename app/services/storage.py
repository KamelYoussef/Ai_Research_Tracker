from app.models.response import Response
from sqlalchemy.orm import Session

def store_response(db: Session, product: str, location: str, total_count: int):
    # Create a new Response object
    response = Response(
        product=product,
        location=location,
        total_count=total_count
    )

    # Add the response to the session and commit
    db.add(response)
    db.commit()
    db.refresh(response)  # Refresh to get the new data (e.g., id after insert)
    return response  # Return the stored response object
