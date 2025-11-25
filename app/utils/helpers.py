import yaml
from app.services.ai_api import get_ai_response
from app.nlp.extractor import find_words_in_texts, find_competitors_in_texts, ranking, get_sentiment_score
from concurrent.futures import ThreadPoolExecutor
from app.models.response import Response
from app.models.sources import Sources
from app.models.maps import Maps
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from passlib.context import CryptContext
import time
from threading import Semaphore
from collections import Counter
from dotenv import load_dotenv
import os
import requests

semaphore = Semaphore(7)  # Limit to 10 concurrent threads
SECRET_KEY = "d4f63gD82!d@#90p@KJ1$#F94mcP@Q43!gf2"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()
load_dotenv()
API_KEY_MAPS = os.getenv('API_KEY_MAPS')
BASE_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'


def load_config(config_file):
    with open(config_file, 'r') as file:
        config = yaml.safe_load(file)
    return config


def load_and_validate_config(config_path):
    """
    Load and validate the configuration file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Loaded configuration dictionary.

    Raises:
        RuntimeError: If the configuration is invalid or cannot be loaded.
    """
    try:
        config = load_config(config_path)
        required_keys = ['locations', 'search_phrases', 'products']
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ValueError(f"Missing configuration keys: {', '.join(missing_keys)}")
        return config
    except Exception as e:
        raise RuntimeError(f"Error loading configuration: {str(e)}")


def process_product_location(product, location, search_phrases, ai_platform, prompt, competitors):
    """
    Generate a prompt, get AI response, and find matches in the response.

    Args:
        product (str): Product name.
        location (str): Location name.
        search_phrases (list): List of search phrases.

    Returns:
        dict: Dictionary containing product, location, match details, and AI response.
    """
    try:
        if prompt is None:
            prompt = f"where can I get a {product} insurance quote in {location}"

        query = prompt.format(keyword=product, location=location)
        ai_response, sources = get_ai_response(query+" CANADA", ai_platform)
        rank = ranking(ai_response, search_phrases)
        sentiment = get_sentiment_score(ai_response, search_phrases)
        match_results = find_words_in_texts(ai_response, search_phrases)
        competitors = find_competitors_in_texts(ai_response, competitors)

        has_matches = int(any(match_results.values()))
        return {
            "product": product,
            "location": location,
            "ai_response": ai_response,
            "total_count": has_matches,
            "matches": match_results,
            "competitors": competitors,
            "rank": rank,
            "sentiment": sentiment,
            "sources": sources
        }
    except Exception as e:
        print(f"[ERROR] {product} - {location}: {e}")
        return {
            "product": product,
            "location": location,
            "ai_response": "",
            "total_count": 0,
            "matches": {},
            "competitors": {"co-operators": 0, "westland": 0, "brokerlink": 0},
            "rank": None,
            "sentiment": None,
            "sources": [],
            "error": str(e)
        }


def process_product_location_with_delay(product, location, search_phrases, ai_platform, prompt, competitors):
    # Wait until we are allowed to acquire the semaphore (this will throttle the rate)
    semaphore.acquire()
    if ai_platform == 'CLAUDE':
        RPM = 1
    else:
        RPM = 50

    SECONDS_PER_REQUEST = 60 / RPM
    try:
        start_time = time.time()
        result = process_product_location(product, location, search_phrases, ai_platform, prompt, competitors)
        elapsed = time.time() - start_time
        # Sleep just enough to respect RPM
        if elapsed < SECONDS_PER_REQUEST:
            time.sleep(SECONDS_PER_REQUEST - elapsed)
        return result
    finally:
        semaphore.release()


def track_responses(ai_platform, config_path, locations=None, products=None, prompt=None, script=None):
    """
    Tracks responses from the AI platform based on provided or configured locations and products.

    :param ai_platform: The AI platform to query.
    :param config_path: Path to the configuration file.
    :param locations: List of locations to process. Optional. Overrides config if provided.
    :param products: List of products to process. Optional. Overrides config if provided.
    :param prompt: Prompt of the search.
    :param script: If provided, use `process_product_location` instead of `process_product_location_with_delay`.
    :return: Tuple of AI responses and results.
    """
    # Load configuration for search_phrases
    config = load_and_validate_config(config_path)

    # Use provided locations and products if available, otherwise fallback to config
    locations = locations if locations is not None else config["locations"]
    products = products if products is not None else config["products"]
    search_phrases = config["search_phrases"]
    competitors = config["competitors"]

    # Determine the function to use
    processing_function = process_product_location if script is not None else process_product_location_with_delay

    results = []
    ai_responses = []  # List to collect all AI responses

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                processing_function, product, location, search_phrases, ai_platform, prompt, competitors
            )
            for product in products
            for location in locations
        ]

        # Collect results and AI responses as tasks complete
        for future in futures:
            try:
                result = future.result()
                result_data = {key: value for key, value in result.items() if key != 'ai_response'}
                results.append(result_data)
                if result.get("ai_response"):
                    ai_responses.append(f"{result['ai_response']}\n")
            except Exception as e:
                print(f"Error processing task: {e}")

    return ai_responses, results


def get_counts_from_config(config_path):
    """
    Get the number of locations and products from the config file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        int: Number of products and locations.
    """
    try:
        config = load_and_validate_config(config_path)

        # Count locations and products
        n_provinces = 6 # provinces in locations in config.yml
        n_locations = len(config['locations']) - n_provinces
        n_products = len(config['products'])
        n_ai_platforms = len(config['ai_platforms'])

        # Return the counts
        return n_locations, n_products, n_ai_platforms

    except Exception as e:
        raise RuntimeError(f"Error retrieving counts from configuration: {str(e)}")


def aggregate_total_by_product(db: Session, month: str, is_city: bool = True):
    """
    Aggregate total_count by product for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.
        is_city

    Returns:
        List[dict]: Aggregated totals by product.
    """
    results = (
        db.query(
            Response.product,
            func.sum(Response.total_count).label("total_count"),
            func.sum(Response.competitor_1).label("competitor_1"),
            func.sum(Response.competitor_2).label("competitor_2"),
            func.sum(Response.competitor_3).label("competitor_3"),
            Response.day,
            Response.ai_platform
        )
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .group_by(Response.day, Response.product, Response.ai_platform)
        .all()
    )
    print(results)
    return [
        {
            "product": r[0],
            "total_count": r[1],
            "competitor_1": r[2],
            "competitor_2": r[3],
            "competitor_3": r[4],
            "day": r[5],
            "ai_platform": r[6]
        }
        for r in results
    ]


def aggregate_total_by_location(db: Session, month: str, is_city: bool = True):
    """
    Aggregate total_count by location for a given month, including competitor data.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        List[dict]: Aggregated totals by location.
    """
    results = (
        db.query(
            Response.location,
            func.sum(Response.total_count).label("total_count"),
            func.sum(Response.competitor_1).label("competitor_1"),
            func.sum(Response.competitor_2).label("competitor_2"),
            func.sum(Response.competitor_3).label("competitor_3"),
            Response.day,
            Response.ai_platform
        )
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .group_by(Response.day, Response.location, Response.ai_platform)
        .all()
    )
    return [
        {
            "location": r[0],
            "total_count": r[1],
            "competitor_1": r[2],
            "competitor_2": r[3],
            "competitor_3": r[4],
            "day": r[5],
            "ai_platform": r[6],
        }
        for r in results
    ]


def aggregate_total_by_product_and_location(db: Session, month: str, is_city: bool = True):
    """
    Aggregate total_count by product and location for a given month, including competitor data.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        List[dict]: Aggregated totals by product and location.
    """
    results = (
        db.query(
            Response.product,
            Response.location,
            func.sum(Response.total_count).label("total_count"),
            func.sum(Response.competitor_1).label("competitor_1"),
            func.sum(Response.competitor_2).label("competitor_2"),
            func.sum(Response.competitor_3).label("competitor_3"),
            Response.day,
            Response.ai_platform
        )
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .group_by(Response.product, Response.location, Response.day, Response.ai_platform)
        .all()
    )
    return [
        {
            "product": r[0],
            "location": r[1],
            "total_count": r[2],
            "competitor_1": r[3],
            "competitor_2": r[4],
            "competitor_3": r[5],
            "day": r[6],
            "ai_platform": r[7],
        }
        for r in results
    ]


def calculate_score_ai(db: Session, month: str, config_path, flag_competitor, is_city: bool = True):
    """
    Calculate the AI score by summing the total_count for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.
        config_path (str): Path to the configuration file.
        flag_competitor (str): Flag representing the competitor.

    Returns:
        float: Calculated AI score.
    """
    # Query to sum the total_count for all products, locations, or combinations in the month
    result = db.query(func.coalesce(func.sum(getattr(Response, flag_competitor)), 0)) \
        .filter(Response.date == month) \
        .filter(Response.is_city == is_city) \
        .scalar()

    unique_days = db.query(func.count(distinct(Response.day))) \
        .filter(Response.date == month) \
        .filter(Response.is_city == is_city) \
        .scalar()

    _, n_products, _ = get_counts_from_config(config_path)

    n_locations = db.query(func.count(distinct(Response.location))) \
        .filter(Response.date == month) \
        .filter(Response.is_city == is_city) \
        .scalar() - 6 # number of provinces

    if is_city is False:
        n_locations = 6 # number of provinces
    n_ai_platforms = db.query(func.count(distinct(Response.ai_platform))) \
        .filter(Response.date == month) \
        .filter(Response.is_city == is_city) \
        .scalar()
    score = result / (n_locations * n_products * n_ai_platforms) / unique_days * 100

    return score if score else 0


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Generate a JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Validates the provided JWT token.
    """
    token = credentials.credentials  # Extract the token from the header
    try:
        # Decode and validate the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        return payload  # Return token payload if valid
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def admin_required(payload: dict = Depends(validate_token)):
    """
    Only allows users with the 'admin' role to proceed.
    """
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action",
        )
    return payload


def calculate_rank(db: Session, month: str, is_city: bool = True):
    """
    Calculate the average rank for a given month, optionally filtered by city status.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.
        is_city (bool): Filter rows based on whether location is a city. Default is True.

    Returns:
        avg_rank : Average rank for the given month, or None if no data is found.
    """
    avg_rank = (
        db.query(func.avg(Response.rank))
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .scalar()
    )
    return avg_rank  # Returns None if no records are found


def calculate_rank_by_platform(db: Session, month: str, ai_platform: str, is_city: bool = True):
    """
    Calculate the average rank for a specific AI platform and month, filtered by city status.

    Args:
        db (Session): SQLAlchemy session.
        month (str): The month in 'YYYYMM' format.
        ai_platform (str): The name of the AI platform.
        is_city (bool): Filter rows based on whether location is a city. Default is True.

    Returns:
        avg_rank: The average rank, or None if no data is found.
    """
    avg_rank = (
        db.query(func.avg(Response.rank))
        .filter(Response.ai_platform == ai_platform)
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .scalar()
    )
    return avg_rank


def get_aggregated_sources(db: Session, ai_platform: str, month: str) -> dict:
    """
    Retrieve and aggregate the 'sources' dictionaries from all matching rows.

    Args:
        db: SQLAlchemy Session
        ai_platform: The AI platform name
        date: The date string (e.g., "202505")

    Returns:
        A single dictionary with domain names as keys and summed counts as values.
    """
    results = db.query(Sources.sources).filter(
        Sources.ai_platform == ai_platform,
        Sources.date == month
    ).all()

    total_sources = Counter()

    for row in results:
        if row.sources:
            total_sources.update(row.sources)

    return dict(sorted(total_sources.items(), key=lambda x: x[1], reverse=True))


def calculate_sentiment(db: Session, month: str, is_city: bool = True):
    """
    Calculate the average sentiment for a given month, optionally filtered by city status.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.
        is_city (bool): Filter rows based on whether location is a city. Default is True.

    Returns:
        avg_sentiment : Average sentiment for the given month, or None if no data is found.
    """
    avg_sentiment = (
        db.query(func.avg(Response.sentiment))
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .scalar()
    )
    return avg_sentiment


def calculate_sentiment_by_platform(db: Session, month: str, ai_platform: str, is_city: bool = True):
    """
    Calculate the average sentiment for a specific AI platform and month, optionally filtered by city status.

    Args:
        db (Session): SQLAlchemy session.
        ai_platform (str): The name of the AI platform.
        month (str): The month in 'YYYYMM' format.
        is_city (bool): Filter rows based on whether location is a city. Default is True.

    Returns:
        avg_sentiment: The average sentiment, or None if no data is found.
    """
    avg_sentiment = (
        db.query(func.avg(Response.sentiment))
        .filter(Response.ai_platform == ai_platform)
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .scalar()
    )
    return avg_sentiment


def get_insurance_brokers_by_city(config_path):
    results = {}
    config = load_and_validate_config(config_path)
    for location in config["locations"]:
        results[location] = []  # Initialize empty list for each city

        for product in config["products"]:
            query = f"{product} insurance in {location} canada"
            params = {
                'query': query,
                'key': API_KEY_MAPS
            }

            response = requests.get(BASE_URL, params=params)
            data = response.json()

            for place in data.get("results", []):
                name = place.get("name")
                rating = place.get("rating")
                reviews = place.get("user_ratings_total")

                results[location].append({
                    "product": product,
                    "name": name,
                    "rating": rating,
                    "reviews": reviews
                })

            time.sleep(1)  # avoid hitting API rate limits

    return results


def find_target_rank_by_city_and_keyword(results,config_path):
    target_ranks = {}
    config = load_and_validate_config(config_path)

    for location, places in results.items():
        # Group places by keyword
        places_by_keyword = {}
        for place in places:
            product = place.get("product", "unknown")
            places_by_keyword.setdefault(product, []).append(place)

        for product, keyword_places in places_by_keyword.items():
            found_rank = None
            matched_name = None
            matched_rating = None
            matched_reviews = None

            for i, place in enumerate(keyword_places, start=1):
                name = place["name"]
                rating = place.get("rating")
                reviews = place.get("reviews")
                name_lower = name.lower()
                if any(target in name_lower for target in config["search_phrases"]):
                    found_rank = i
                    matched_name = name
                    matched_rating = rating
                    matched_reviews = reviews
                    break

            # Use a tuple key (city, keyword)
            target_ranks[(location, product)] = {
                "rank": found_rank,
                "name": matched_name,
                "rating": matched_rating,
                "reviews": matched_reviews
            }
    data = []
    for (location, product), info in target_ranks.items():
        data.append({
            'location': location,
            'product': product,
            'rank': info.get('rank', 'None'),
            'rating': info.get('rating', 'None'),
            'reviews': info.get('reviews', 'None')
        })

    return data


def aggregate_maps_by_product_and_location(db: Session, month: str, is_city: bool = True):
    """
    Aggregate total_count by product and location for a given month, including competitor data.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        List[dict]: Aggregated totals by product and location.
    """
    results = (
        db.query(
            Maps.product,
            Maps.location,
            func.sum(Maps.rank).label("rank"),
            Maps.day,
            Maps.rating,
            Maps.reviews
        )
        .filter(Maps.date == month)
        .filter(Maps.is_city == is_city)
        .group_by(Maps.product, Maps.location, Maps.day, Maps.rating, Maps.reviews)
        .all()
    )

    return [
        {
            "product": r[0],
            "location": r[1],
            "rank": r[2],
            "day": r[3],
            "rating": r[4],
            "reviews": r[5]
        }
        for r in results
    ]


def calculate_avg_sentiment_by_location_platform(db: Session, month: str, is_city: bool = True):
    """
    Calculate the average sentiment grouped by location and AI platform for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.
        is_city (bool): Filter rows based on whether location is a city. Default is True.

    Returns:
        results (list of dict): Each dict contains location, ai_platform, and avg_sentiment.
    """
    query = (
        db.query(
            Response.location,
            Response.ai_platform,
            func.avg(Response.sentiment).label("avg_sentiment")
        )
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .group_by(Response.location, Response.ai_platform)
        .all()
    )

    results = [
        {"location": loc, "ai_platform": platform, "avg_sentiment": avg}
        for loc, platform, avg in query
    ]
    return results


def calculate_avg_rank_by_location_platform(db: Session, month: str, is_city: bool = True):
    """
    Calculate the average rank grouped by location and AI platform for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.
        is_city (bool): Filter rows based on whether location is a city. Default is True.

    Returns:
        results (list of dict): Each dict contains location, ai_platform, and avg_rank.
    """
    query = (
        db.query(
            Response.location,
            Response.ai_platform,
            func.round(func.avg(Response.rank), 2).label("avg_rank")
        )
        .filter(Response.date == month)
        .filter(Response.is_city == is_city)
        .group_by(Response.location, Response.ai_platform)
        .all()
    )

    results = [
        {"location": loc, "ai_platform": platform, "avg_rank": avg_rank}
        for loc, platform, avg_rank in query
    ]
    return results
