from app.models.response import Response
from sqlalchemy.orm import Session


def store_response(db: Session, product: str, location: str, total_count: int, ai_platform: str, date: str, day: str,
                   competitor_1: str, competitor_2: str, competitor_3: str):
    """
    Store the AI-generated response in the database.

    Args:
    - db: Database session
    - product: The product being queried
    - location: The location of interest
    - total_count: The number of results
    - query: The query made to the AI system
    - response_text: The AI's response

    Returns:
    - The stored Response object
    """
    # Create a new Response object with the data, including the query and response text
    response = Response(
        product=product,
        location=location,
        total_count=total_count,
        ai_platform=ai_platform,
        date=date,
        day=day,
        competitor_1=competitor_1,
        competitor_2=competitor_2,
        competitor_3=competitor_3
    )

    # Add the response to the session and commit
    db.add(response)
    db.commit()  # Save to the database
    db.refresh(response)  # Get the updated data (including the generated id)

    return response  # Return the stored response object
