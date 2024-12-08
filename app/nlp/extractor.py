import re

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
    for phrase in search_phrases:
        # Check if the phrase exists in the text
        matches[phrase] = int(bool(re.search(rf'\b{re.escape(phrase)}\b', text, re.IGNORECASE)))

    return matches