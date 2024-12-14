import yaml
from app.services.ai_api import get_ai_response
from app.nlp.extractor import find_words_in_texts
from concurrent.futures import ThreadPoolExecutor
from app.models.response import Response
from sqlalchemy.orm import Session
from sqlalchemy import func
import os


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


def process_product_location(product, location, search_phrases, ai_platform):
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
        prompt = f"give me the best {product} insurance companies in {location}"
        ai_response = get_ai_response(prompt, ai_platform).content
        match_results = find_words_in_texts(ai_response, search_phrases)

        has_matches = int(any(match_results.values()))
        return {
            "product": product,
            "location": location,
            "ai_response": ai_response,
            "total_count": has_matches,
            "matches": match_results
        }
    except Exception as e:
        return {
            "product": product,
            "location": location,
            "ai_response": "",
            "error": str(e)
        }


def track_responses(ai_platform, config_path, locations=None, products=None):
    """
    Tracks responses from the AI platform based on provided or configured locations and products.

    :param ai_platform: The AI platform to query.
    :param config_path: Path to the configuration file.
    :param locations: List of locations to process. Optional. Overrides config if provided.
    :param products: List of products to process. Optional. Overrides config if provided.
    :return: Tuple of AI responses and results.
    """
    # Load configuration for search_phrases
    config = load_and_validate_config(config_path)

    # Use provided locations and products if available, otherwise fallback to config
    locations = locations if locations is not None else config["locations"]
    products = products if products is not None else config["products"]
    search_phrases = config["search_phrases"]

    results = []
    ai_responses = []  # List to collect all AI responses

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_product_location, product, location, search_phrases, ai_platform
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
        db.query(Response.product, func.sum(Response.total_count).label("total_count"), Response.day, Response.ai_platform)
        .filter(Response.date == month)
        .group_by(Response.day, Response.product, Response.ai_platform)
        .all()
    )
    print(results)
    return [{"product": r[0], "total_count": r[1], "day": r[2], "ai_platform": r[3]} for r in results]


def aggregate_total_by_location(db: Session, month: str):
    """
    Aggregate total_count by location for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        List[dict]: Aggregated totals by location.
    """
    results = (
        db.query(Response.location, func.sum(Response.total_count).label("total_count"), Response.day, Response.ai_platform)
        .filter(Response.date == month)
        .group_by(Response.day, Response.location, Response.ai_platform)
        .all()
    )
    return [{"location": r[0], "total_count": r[1], "day": r[2], "ai_platform": r[3]} for r in results]


def aggregate_total_by_product_and_location(db: Session, month: str):
    """
    Aggregate total_count by product and location for a given month.

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
            Response.day,
            Response.ai_platform
        )
        .filter(Response.date == month)
        .group_by(Response.product, Response.location, Response.day, Response.ai_platform)
        .all()
    )
    return [
                {"product": r[0],
                 "location": r[1],
                 "total_count": r[2],
                 "day": r[3],
                 "ai_platform": r[4]
                 }
                for r in results
            ]


def calculate_score_ai(db: Session, month: str, config_path):
    """
    Calculate the score_ai by summing the total_count for a given month.

    Args:
        db (Session): SQLAlchemy session.
        month (str): Month in YYYYMM format.

    Returns:
        int: Total sum of total_count for the given month.
    """
    # Query to sum the total_count for all products, locations, or combinations in the month
    result = db.query(func.sum(Response.total_count)).filter(Response.date == month).scalar()
    n_locations, n_products, n_ai_platforms = get_counts_from_config(config_path)
    score = result / (n_locations * n_products * n_ai_platforms) / days_in_month(month)* 100
    return score if score else 0  # Return 0 if no records found


def days_in_month(input_date):
    """
    Returns the number of days in a given month based on a "YYYYMM" string format.

    Parameters:
    input_date (str): Date in the format "YYYYMM" (e.g., "202412" for December 2024)

    Returns:
    int: Number of days in the month
    """
    # Validate input format
    if len(input_date) != 6 or not input_date.isdigit():
        raise ValueError("Input must be a string in the format 'YYYYMM'")

    # Extract year and month
    year = int(input_date[:4])
    month = int(input_date[4:])

    # Validate month range
    if month < 1 or month > 12:
        raise ValueError("Month must be between 01 and 12")

    # List of days in each month
    days_per_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Check for February in a leap year
    if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
        return 29

    return days_per_month[month - 1]
