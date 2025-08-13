import re
import json
from google import genai
from app.config import GEMINI_API_KEY
import time
import random

client_gemini = genai.Client(api_key=GEMINI_API_KEY)


def find_words_in_texts(text, search_phrases):
    """
    Search for phrases in the given text and return match results.

    Args:
        text (str): The text to search in.
        search_phrases (list): List of phrases to search for.

    Returns:
        dict: Dictionary with phrases as keys and match indicators as values.
    """
    matches = {}

    # Handle None or invalid text input gracefully
    if not isinstance(text, str):
        text = ""

    for phrase in search_phrases:
        # Check if the phrase exists in the text
        matches[phrase] = int(bool(
            re.search(rf'\b{re.escape(phrase)}\b', text, re.IGNORECASE)
        ))

    return matches


def find_competitors_in_texts(text, competitors):
    """
    Search for phrases in the given text and return match results.

    Args:
        text (str): The text to search in.
        competitors (list): List of phrases to search for.

    Returns:
        dict: Dictionary with phrases as keys and match indicators as values.
    """
    matches = {}

    # Handle None or invalid text input gracefully
    if not isinstance(text, str):
        text = ""

    for phrase in competitors:
        # Check if the phrase exists in the text
        matches[phrase] = int(bool(
            re.search(rf'\b{re.escape(phrase)}\b', text, re.IGNORECASE)
        ))

    return matches


def extract_organizations_gemini(text, retries=3, backoff=5):
    for attempt in range(retries):
        try:
            response = client_gemini.models.generate_content(
                model="gemini-1.5-flash",
                contents=(
                    "Extract only insurance provider organization names in order of appearance "
                    "from the following text and return them as a JSON array:\n\n"
                    f"{text}\n\n"
                )
            )
            raw = response.text.strip()
            cleaned = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
            return json.loads(cleaned)

        except json.JSONDecodeError:
            print("❌ Failed to parse response as JSON. Raw output:")
            print(cleaned)
            return []

        except Exception as e:
            if "503" in str(e) or "Service Unavailable" in str(e):
                wait_time = backoff * (2 ** attempt)
                print(f"⚠️ 503 error — retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                raise
    # If all retries fail
    print("❌ Gemini request failed after retries.")
    return []


def ranking(text, search_phrases):
    organizations_lower = [org.lower() for org in extract_organizations_gemini(text)]
    aliases_lower = [alias.lower() for alias in search_phrases]
    for i, org in enumerate(organizations_lower):
        for alias in aliases_lower:
            if alias in org:
                rank = i + 1
                return rank
    return None


def extract_sentiment(text, retries=3, backoff=2):
    """
    Extract sentiment scores for insurance providers using Gemini,
    retrying on 503 or transient errors, and returning [] on failure.
    """
    for attempt in range(retries):
        try:
            response = client_gemini.models.generate_content(
                model="gemini-1.5-flash",
                contents=(
                    "Extract only the names of insurance provider organizations and their associated sentiment scores "
                    "from the text below. Return the results as a JSON array. "
                    "Each object in the array should have two keys: "
                    "'organization' and 'sentiment_score' (between -1 and 1). "
                    "Do not include any extra text or explanations — only return the JSON array:\n\n"
                    f"{text}\n\n"
                )
            )
            raw = response.text.strip()
            cleaned = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
            return json.loads(cleaned)

        except json.JSONDecodeError:
            print("❌ Failed to parse sentiment JSON. Raw output:")
            print(cleaned)
            return []

        except Exception as e:
            if "503" in str(e) or "Service Unavailable" in str(e):
                wait_time = backoff ** attempt + random.uniform(0, 1)
                print(f"⚠️ 503 error — retrying in {wait_time:.1f} seconds...")
                time.sleep(wait_time)
            else:
                raise

    print("❌ Sentiment extraction failed after retries.")
    return []


def get_sentiment_score(data, search_phrases):
    text = extract_sentiment(data)
    search_phrases_lower = [phrase.lower() for phrase in search_phrases]

    for entry in text:
        org_name_lower = entry['organization'].lower()
        for alias in search_phrases_lower:
            if alias in org_name_lower:
                return entry['sentiment_score']

    return None
