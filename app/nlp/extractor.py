import re
import json
from google import genai
from app.config import GEMINI_API_KEY

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


def extract_organizations_gemini(text):
    response = client_gemini.models.generate_content(
        model="gemini-1.5-flash",
        contents=f"Extract only insurances providers organization names in order of appearance from the following text and return them as a JSON array:\n\n{text}\n\n")

    raw = response.text.strip()
    cleaned = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print("❌ Failed to parse response as JSON. Raw output:")
        print(cleaned)
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


def extract_sentiment(text):
    response = client_gemini.models.generate_content(
        model="gemini-1.5-flash",
        contents=f"Extract only the names of insurance provider organizations and their associated sentiment scores \
        from the text below. Return the results as a JSON array. Each object in the array should have two keys:\
    'organization': the full name of the insurance provider 'sentiment_score': a numeric score between -1 and 1 \
    indicating the overall sentiment toward the organization (where -1 is very negative, 0 is neutral, and 1 is very\
     positive) \n Do not include any extra text or explanations — only return the JSON array.:\n\n{text}\n\n")

    raw = response.text.strip()
    cleaned = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print("❌ Failed to parse response as JSON. Raw output:")
        print(cleaned)
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
