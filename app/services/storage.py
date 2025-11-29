from app.models.response import Response
from app.models.sources import Sources
from app.models.maps import Maps
from sqlalchemy.orm import Session


def store_response(db: Session, product: str, location: str, total_count: int, ai_platform: str, date: str, day: str,
                   competitor_1: str, competitor_2: str, competitor_3: str, competitor_4: str, rank: int, sentiment: float):
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
    provinces = ['Manitoba', 'Alberta', 'British Columbia', 'Saskatchewan', 'Ontario', 'Canada']

    # Create a new Response object with the data, including the query and response text
    response = Response(
        product=product,
        location=location,
        is_city=True if location not in provinces else False,
        total_count=total_count,
        ai_platform=ai_platform,
        date=date,
        day=day,
        competitor_1=competitor_1,
        competitor_2=competitor_2,
        competitor_3=competitor_3,
        competitor_4=competitor_4,
        rank=rank,
        sentiment=sentiment
    )

    # Add the response to the session and commit
    db.add(response)
    db.commit()  # Save to the database
    db.refresh(response)  # Get the updated data (including the generated id)

    return response  # Return the stored response object


def store_sources(
    db: Session,
    ai_platform: str,
    date: str,
    day: str,
    sources: dict
):
    """
    Store the sources dict as a new row in the database.

    Args:
        db: SQLAlchemy Session
        ai_platform: AI platform name
        date: date string, e.g. "202505"
        day: day string, e.g. "22"
        sources: dictionary of source URLs and counts

    Returns:
        The inserted Sources object
    """
    source_record = Sources(
        ai_platform=ai_platform,
        date=date,
        day=day,
        sources=sources
    )
    db.add(source_record)
    db.commit()
    db.refresh(source_record)
    return source_record


def store_maps(db: Session, product: str, location: str, rank: int, date: str, day: str,
               rating: float, reviews: int):
    """
    Store the API MAPS response in the database.

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
    provinces = ['Manitoba', 'Alberta', 'British Columbia', 'Saskatchewan', 'Ontario', 'Canada']

    # Create a new Response object with the data, including the query and response text
    response = Maps(
        product=product,
        location=location,
        is_city=True if location not in provinces else False,
        rank=rank,
        date=date,
        day=day,
        rating=rating,
        reviews=reviews
    )

    # Add the response to the session and commit
    db.add(response)
    db.commit()  # Save to the database
    db.refresh(response)  # Get the updated data (including the generated id)

    return response  # Return the stored response object