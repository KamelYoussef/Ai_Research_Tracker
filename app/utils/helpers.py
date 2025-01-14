import yaml
from app.services.ai_api import get_ai_response
from app.nlp.extractor import find_words_in_texts, find_competitors_in_texts
from concurrent.futures import ThreadPoolExecutor
from app.models.response import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from jose import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from passlib.context import CryptContext

SECRET_KEY = "d4f63gD82!d@#90p@KJ1$#F94mcP@Q43!gf2"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
security = HTTPBearer()


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
            prompt = f"give me the best {product} insurance in {location}"

        query = prompt.format(keyword=product, location=location)
        ai_response = get_ai_response(query, ai_platform)
        match_results = find_words_in_texts(ai_response, search_phrases)
        competitors = find_competitors_in_texts(ai_response, competitors)

        has_matches = int(any(match_results.values()))
        return {
            "product": product,
            "location": location,
            "ai_response": ai_response,
            "total_count": has_matches,
            "matches": match_results,
            "competitors": competitors
        }
    except Exception as e:
        return {
            "product": product,
            "location": location,
            "ai_response": "",
            "error": str(e)
        }


def track_responses(ai_platform, config_path, locations=None, products=None, prompt=None):
    """
    Tracks responses from the AI platform based on provided or configured locations and products.

    :param ai_platform: The AI platform to query.
    :param config_path: Path to the configuration file.
    :param locations: List of locations to process. Optional. Overrides config if provided.
    :param products: List of products to process. Optional. Overrides config if provided.
    :param prompt: Prompt of the search
    :return: Tuple of AI responses and results.
    """
    # Load configuration for search_phrases
    config = load_and_validate_config(config_path)

    # Use provided locations and products if available, otherwise fallback to config
    locations = locations if locations is not None else config["locations"]
    products = products if products is not None else config["products"]
    search_phrases = config["search_phrases"]
    competitors = config["competitors"]

    results = []
    ai_responses = []  # List to collect all AI responses

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_product_location, product, location, search_phrases, ai_platform, prompt, competitors
            )
            for product in products
            for location in locations
        ]

        # Collect results and AI responses as tasks complete
        for future in futures:
            result = future.result()
            result_data = {key: value for key, value in result.items() if key != 'ai_response'}
            results.append(result_data)
            if result.get("ai_response"):
                ai_responses.append(
                    f"{result['ai_response']}\n"
                )
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
        n_locations = len(config['locations'])
        n_products = len(config['products'])
        n_ai_platforms = len(config['ai_platforms'])

        # Return the counts
        return n_locations, n_products, n_ai_platforms

    except Exception as e:
        raise RuntimeError(f"Error retrieving counts from configuration: {str(e)}")


def aggregate_total_by_product(db: Session, month: str):
    """
    Aggregate total_count by product for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

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


def aggregate_total_by_location(db: Session, month: str):
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


def aggregate_total_by_product_and_location(db: Session, month: str):
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


def calculate_score_ai(db: Session, month: str, config_path, flag_competitor):
    """
    Calculate the score_ai by summing the total_count for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        int: Total sum of total_count for the given month.
    """
    # Query to sum the total_count for all products, locations, or combinations in the month
    result = db.query(func.sum(getattr(Response, flag_competitor))).filter(Response.date == month).scalar()
    n_locations, n_products, n_ai_platforms = get_counts_from_config(config_path)
    score = result / (n_locations * n_products * n_ai_platforms) / 4 * 100 # 4 is for 4 weeks in the month
    return score if score else 0  # Return 0 if no records found


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
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
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
