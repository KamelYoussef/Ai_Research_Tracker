from app.models.response import Response
from sqlalchemy.orm import Session

def store_response(db: Session, product: str, location: str, total_count: int, query: str, response_text: str):
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
        query=query,  # Store the original query
        response_text=response_text  # Store the response text generated by AI
    )

    # Add the response to the session and commit
    db.add(response)
    db.commit()  # Save to the database
    db.refresh(response)  # Get the updated data (including the generated id)

    return response  # Return the stored response object