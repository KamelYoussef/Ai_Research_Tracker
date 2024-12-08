import yaml
from app.services.ai_api import get_ai_response
from app.nlp.extractor import find_words_in_texts
from concurrent.futures import ThreadPoolExecutor
from app.models.response import Response
from sqlalchemy.orm import Session
from sqlalchemy import func


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


def track_responses(ai_platfrom):
    config_path = "../config.yml"
    config = load_and_validate_config(config_path)

    results = []
    ai_responses = []  # List to collect all AI responses

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_product_location, product, location, config["search_phrases"], ai_platfrom
            )
            for product in config["products"]
            for location in config["locations"]
        ]

        # Collect results and AI responses as tasks complete
        for future in futures:
            result = future.result()
            result_data = {key: value for key, value in result.items() if key != 'ai_response'}
            results.append(result_data)
            if result.get("ai_response"):
                ai_responses.append(
                    f"Product: {result['product']}, Location: {result['location']}\n{result['ai_response']}\n"
                )
    return ai_responses, results


def get_counts_from_config():
    """
    Get the number of locations and products from the config file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        int: Number of products and locations.
    """
    try:
        config_path = "../config.yml"
        config = load_and_validate_config(config_path)

        # Count locations and products
        n_locations = len(config['locations'])
        n_products = len(config['products'])

        # Return the counts
        return n_locations, n_products

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
        db.query(Response.product, func.sum(Response.total_count).label("total_count"), Response.day)
        .filter(Response.date == month)
        .group_by(Response.day, Response.product)
        .all()
    )
    print(results)
    return [{"product": r[0], "total_count": r[1], "day": r[2]} for r in results]


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
        db.query(Response.location, func.sum(Response.total_count).label("total_count"), Response.day)
        .filter(Response.date == month)
        .group_by(Response.day, Response.location)
        .all()
    )
    return [{"location": r[0], "total_count": r[1], "day": r[2]} for r in results]


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
        )
        .filter(Response.date == month)
        .group_by(Response.product, Response.location)
        .all()
    )
    return [
        {"product": r[0], "location": r[1], "total_count": r[2]} for r in results
    ]


def calculate_score_ai(db: Session, month: str):
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
    return result if result else 0  # Return 0 if no records found


