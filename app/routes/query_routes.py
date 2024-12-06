from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
#from app.nlp.extractor import find_words_in_texts  # Make sure your helper function is imported
from app.services.ai_api import get_ai_response
from app.services.storage import store_response
from app.dependencies import get_db
from app.utils.helpers import load_config, find_words_in_texts
from concurrent.futures import ThreadPoolExecutor


router = APIRouter()


@router.post("/submit_query_with_default/")
async def submit_query_with_default(db: Session = Depends(get_db)):
    ai_responses, results = first()
    # Store the response and AI response in the database
    #store_response(db, response=ai_responses, platform="OpenAI")

    return {"message": "Query submitted successfully", "search_results": results, "ai_response": ai_responses}


@router.post("/submit_query/")
async def submit_query():
    prompt ="why sky is blue"
    ai_response = get_ai_response(prompt, ai_platform="OpenAI")
    print(ai_response)

    #results = find_words_in_texts(text, search_phrases, product, location)

    # Save the result in the database
    #response = store_response(db, product=product, location=location, total_count=results["total_count"])

    return {"message": "Query submitted successfully", "response": ai_response}


@router.get("/get_responses/")
def get_responses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    responses = get_responses(db, skip=skip, limit=limit)
    return {"responses": responses}


@router.post("/store_response/")
def store_query_response(product: str, location: str, total_count: int, db: Session = Depends(get_db)):
    # Store the response and return the object
    response = store_response(db=db, product=product, location=location, total_count=total_count)
    return response  # Optionally return the stored response object


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

def process_product_location(product, location, search_phrases, ai):
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
        ai_response = get_ai_response(prompt, ai).content
        matches = find_words_in_texts(ai_response, search_phrases, product, location)
        return {
            "product": product,
            "location": location,
            "ai_response": ai_response,
            **matches
        }
    except Exception as e:
        return {
            "product": product,
            "location": location,
            "ai_response": "",
            "error": str(e)
        }

def first():
    config_path = "app/config.yml"
    config = load_and_validate_config(config_path)

    results = []
    ai_responses = []  # List to collect all AI responses

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                process_product_location, product, location, config["search_phrases"],"chatgpt"
            )
            for product in config["products"]
            for location in config["locations"]
        ]

        # Collect results and AI responses as tasks complete
        for future in futures:
            result = future.result()
            # Exclude ai_response from DataFrame
            result_data = {key: value for key, value in result.items() if key != 'ai_response'}
            results.append(result_data)  # Append without AI response
            if result.get("ai_response"):
                ai_responses.append(
                    f"Product: {result['product']}, Location: {result['location']}\n{result['ai_response']}\n"
                )
    return ai_responses, results